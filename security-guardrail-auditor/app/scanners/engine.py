from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

from app.scanners.types import RawFinding

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("hardcoded_password", re.compile(r"(?i)\bpassword\s*=\s*[\"'][^\"']+[\"']")),
    ("hardcoded_secret", re.compile(r"(?i)\b(secret|api_key|token|aws_secret_access_key)\s*=\s*[\"'][^\"']+[\"']")),
]


def iter_resources(doc: dict[str, Any]) -> Iterator[tuple[str, str, dict[str, Any], str | None]]:
    """Yield (resource_type, resource_name, attributes, nested_key)."""
    for block in doc.get("resource", []) or []:
        if not isinstance(block, dict):
            continue
        for res_type, instances in block.items():
            if not isinstance(instances, dict):
                continue
            for name, attrs in instances.items():
                if isinstance(attrs, dict):
                    yield res_type, name, attrs, None


def _boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _cidr_open_to_world(cidrs: Any) -> bool:
    if isinstance(cidrs, str):
        cidrs = [cidrs]
    if not isinstance(cidrs, list):
        return False
    return any(c in {"0.0.0.0/0", "::/0"} for c in cidrs if isinstance(c, str))


def _ingress_blocks(attrs: dict[str, Any]) -> list[dict[str, Any]]:
    ing = attrs.get("ingress")
    if ing is None:
        return []
    if isinstance(ing, dict):
        return [ing]
    if isinstance(ing, list):
        return [row for row in ing if isinstance(row, dict)]
    return []


def collect_raw_findings(
    parsed_files: Iterable[tuple[str, dict[str, Any]]],
    raw_text_by_path: dict[str, str],
) -> list[RawFinding]:
    findings: list[RawFinding] = []
    docs = list(parsed_files)
    resource_index: list[tuple[str, str, str, dict[str, Any]]] = []

    for path, doc in docs:
        for res_type, name, attrs, _ in iter_resources(doc):
            resource_index.append((path, res_type, name, attrs))

    # S3 public exposure
    for path, res_type, name, attrs in resource_index:
        if res_type == "aws_s3_bucket":
            acl = attrs.get("acl")
            if isinstance(acl, str) and acl.lower() in {"public-read", "public-read-write"}:
                findings.append(
                    RawFinding(
                        rule_id="S3_PUBLIC_ACL",
                        severity="critical",
                        resource_type=res_type,
                        resource_name=name,
                        title="S3 bucket uses a public ACL",
                        description=f"Bucket `{name}` sets acl = {acl!r}, which can allow public object reads or writes.",
                        remediation="Use private ACL, enforce bucket policies that deny public access, and enable S3 Block Public Access.",
                        terraform_fix_example='acl = "private"\n# plus aws_s3_bucket_public_access_block with block_public_acls = true',
                        file_path=path,
                    )
                )
            if attrs.get("website"):
                findings.append(
                    RawFinding(
                        rule_id="S3_WEBSITE_LEGACY",
                        severity="medium",
                        resource_type=res_type,
                        resource_name=name,
                        title="S3 static website configuration detected",
                        description="Legacy website endpoints are easy to misconfigure for public reads.",
                        remediation="Prefer CloudFront with OAI/OAC and private buckets.",
                        terraform_fix_example="# Prefer aws_s3_bucket_website_configuration + CloudFront origin access control",
                        file_path=path,
                    )
                )

        if res_type == "aws_s3_bucket_public_access_block":
            if (
                _boolish(attrs.get("block_public_acls")) is False
                or _boolish(attrs.get("block_public_policy")) is False
            ):
                findings.append(
                    RawFinding(
                        rule_id="S3_PUBLIC_ACCESS_BLOCK_DISABLED",
                        severity="high",
                        resource_type=res_type,
                        resource_name=name,
                        title="S3 Block Public Access partially disabled",
                        description="Public access blocks should all be true for data buckets.",
                        remediation="Set block_public_acls, block_public_policy, ignore_public_acls, ignore_public_policy to true.",
                        terraform_fix_example="block_public_acls = true\nblock_public_policy = true\nignore_public_acls = true\nignore_public_policy = true",
                        file_path=path,
                    )
                )

        if res_type == "aws_security_group":
            for rule in _ingress_blocks(attrs):
                proto = str(rule.get("protocol", "tcp")).lower()
                if not _cidr_open_to_world(rule.get("cidr_blocks")):
                    continue
                fp_s, tp_s = rule.get("from_port"), rule.get("to_port")
                try:
                    fp = int(fp_s) if fp_s is not None else None
                    tp = int(tp_s) if tp_s is not None else None
                except (TypeError, ValueError):
                    fp = tp = None

                if proto in {"-1", "all"} and fp == 0 and tp == 0:
                    findings.append(
                        RawFinding(
                            rule_id="SG_ALL_TRAFFIC_OPEN",
                            severity="critical",
                            resource_type=res_type,
                            resource_name=name,
                            title="Security group allows all protocols from the internet",
                            description="Ingress uses from_port/to_port 0 with protocol -1/all from 0.0.0.0/0.",
                            remediation="Replace with least-privilege rules per application port.",
                            terraform_fix_example="# Restrict protocol/ports + CIDRs to minimum required",
                            file_path=path,
                        )
                    )
                    continue

                if fp is None or tp is None:
                    continue
                if proto not in {"tcp", "-1", "all"}:
                    continue

                if fp <= 22 <= tp:
                    findings.append(
                        RawFinding(
                            rule_id="SG_OPEN_SSH",
                            severity="critical",
                            resource_type=res_type,
                            resource_name=name,
                            title="Security group allows SSH from the internet",
                            description="Ingress permits port 22 from 0.0.0.0/0 or ::/0.",
                            remediation="Restrict SSH to bastion IPs or use SSM Session Manager without open SSH.",
                            terraform_fix_example='cidr_blocks = ["10.0.0.0/8"]  # replace with trusted admin CIDRs',
                            file_path=path,
                        )
                    )
                if fp <= 3389 <= tp:
                    findings.append(
                        RawFinding(
                            rule_id="SG_OPEN_RDP",
                            severity="critical",
                            resource_type=res_type,
                            resource_name=name,
                            title="Security group allows RDP from the internet",
                            description="Ingress exposes 3389 to the world.",
                            remediation="Remove open RDP; use VPN or SSM port forwarding.",
                            terraform_fix_example="# Remove 0.0.0.0/0 on 3389; prefer private connectivity",
                            file_path=path,
                        )
                    )

        if res_type == "aws_instance":
            pub = _boolish(attrs.get("associate_public_ip_address"))
            if pub:
                findings.append(
                    RawFinding(
                        rule_id="EC2_PUBLIC_IP",
                        severity="high",
                        resource_type=res_type,
                        resource_name=name,
                        title="EC2 instance requests a public IP",
                        description="associate_public_ip_address is enabled, increasing exposure surface.",
                        remediation="Place workloads in private subnets without public IPs unless required.",
                        terraform_fix_example="associate_public_ip_address = false",
                        file_path=path,
                    )
                )

        if res_type == "aws_db_instance":
            if _boolish(attrs.get("publicly_accessible")):
                findings.append(
                    RawFinding(
                        rule_id="RDS_PUBLIC",
                        severity="critical",
                        resource_type=res_type,
                        resource_name=name,
                        title="RDS instance is publicly accessible",
                        description="publicly_accessible = true exposes the database to the public network path.",
                        remediation="Disable public accessibility; use private subnets and security groups.",
                        terraform_fix_example="publicly_accessible = false",
                        file_path=path,
                    )
                )
            enc = attrs.get("storage_encrypted")
            if _boolish(enc) is False:
                findings.append(
                    RawFinding(
                        rule_id="RDS_UNENCRYPTED",
                        severity="high",
                        resource_type=res_type,
                        resource_name=name,
                        title="RDS storage encryption disabled",
                        description="storage_encrypted is false.",
                        remediation="Enable storage encryption and manage keys via KMS.",
                        terraform_fix_example="storage_encrypted = true\nkms_key_id = aws_kms_key.db.arn",
                        file_path=path,
                    )
                )

        if res_type == "aws_ebs_volume":
            if _boolish(attrs.get("encrypted")) is False:
                findings.append(
                    RawFinding(
                        rule_id="EBS_UNENCRYPTED",
                        severity="high",
                        resource_type=res_type,
                        resource_name=name,
                        title="EBS volume is unencrypted",
                        description="encrypted flag is false.",
                        remediation="Encrypt all volumes by default with a KMS CMK.",
                        terraform_fix_example="encrypted = true\nkms_key_id = aws_kms_key.ebs.arn",
                        file_path=path,
                    )
                )

        if res_type == "aws_dynamodb_table":
            sse = attrs.get("server_side_encryption")
            if isinstance(sse, list):
                sse = sse[0] if sse else None
            if isinstance(sse, dict) and _boolish(sse.get("enabled")) is False:
                findings.append(
                    RawFinding(
                        rule_id="DYNAMODB_SSE_DISABLED",
                        severity="medium",
                        resource_type=res_type,
                        resource_name=name,
                        title="DynamoDB encryption disabled",
                        description="server_side_encryption.enabled is false.",
                        remediation="Enable SSE with AWS owned or customer managed KMS keys.",
                        terraform_fix_example="server_side_encryption { enabled = true }",
                        file_path=path,
                    )
                )

        if res_type in {"aws_network_acl_rule", "aws_default_network_acl"}:
            cidr = attrs.get("cidr_block")
            if cidr == "0.0.0.0/0" and str(attrs.get("rule_action", "")).lower() == "allow":
                findings.append(
                    RawFinding(
                        rule_id="NACL_OPEN_WORLD",
                        severity="medium",
                        resource_type=res_type,
                        resource_name=name,
                        title="Network ACL allows traffic from anywhere",
                        description="Rule allows 0.0.0.0/0 which is rarely appropriate for NACLs.",
                        remediation="Tighten CIDR ranges; prefer security groups for fine-grained control.",
                        terraform_fix_example="# Replace 0.0.0.0/0 with specific CIDR ranges",
                        file_path=path,
                    )
                )

        if res_type in {"aws_iam_role_policy", "aws_iam_user_policy", "aws_iam_policy"}:
            policy_doc = attrs.get("policy")
            if isinstance(policy_doc, dict):
                pol = json.dumps(policy_doc)
            elif isinstance(policy_doc, str):
                pol = policy_doc
            else:
                pol = ""
            if pol and (
                "'Action': '*'" in pol
                or '"Action": "*"' in pol
                or '"Action":"*"' in pol
                or "\\\"Action\\\": \\\"*\\\"" in pol
            ):
                findings.append(
                    RawFinding(
                        rule_id="IAM_WILDCARD_ACTION",
                        severity="critical",
                        resource_type=res_type,
                        resource_name=name,
                        title="IAM policy grants Action=*",
                        description="Wildcard actions grant full API access for the attached principal.",
                        remediation="Replace wildcards with explicit actions required by the workload.",
                        terraform_fix_example='"Action": ["s3:GetObject", "s3:PutObject"]',
                        file_path=path,
                    )
                )
            if pol and (
                "'Resource': '*'" in pol
                or '"Resource": "*"' in pol
                or '"Resource":"*"' in pol
                or "\\\"Resource\\\": \\\"*\\\"" in pol
            ):
                findings.append(
                    RawFinding(
                        rule_id="IAM_WILDCARD_RESOURCE",
                        severity="high",
                        resource_type=res_type,
                        resource_name=name,
                        title="IAM policy grants Resource=*",
                        description="Wildcard resources combined with broad actions are overly permissive.",
                        remediation="Scope resources to ARNs or prefixes.",
                        terraform_fix_example='"Resource": "arn:aws:s3:::my-bucket/*"',
                        file_path=path,
                    )
                )

    # CloudTrail presence (single informational finding if missing)
    has_trail = any(t == "aws_cloudtrail" for _, t, _, _ in resource_index)
    if docs and not has_trail:
        findings.append(
            RawFinding(
                rule_id="CLOUDTRAIL_MISSING",
                severity="medium",
                resource_type="aws_cloudtrail",
                resource_name="*",
                title="No aws_cloudtrail resource detected",
                description="Terraform inputs did not declare CloudTrail; governance and forensics may be gaps.",
                remediation="Add multi-region trails with log file validation and centralized storage.",
                terraform_fix_example='resource "aws_cloudtrail" "audit" { name = "org-audit" is_multi_region_trail = true include_global_service_events = true enable_logging = true }',
                file_path=docs[0][0],
            )
        )

    # Raw text secret scan
    for path, text in raw_text_by_path.items():
        if not path.endswith(".tf"):
            continue
        for rule_id, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(
                    RawFinding(
                        rule_id=rule_id.upper(),
                        severity="critical",
                        resource_type=None,
                        resource_name=None,
                        title="Potential hardcoded secret in Terraform",
                        description="A literal assignment resembling a password/secret was detected.",
                        remediation="Use variables, AWS Secrets Manager, or SSM Parameter Store with secure references.",
                        terraform_fix_example='password = var.db_password # never commit secrets',
                        file_path=path,
                    )
                )
                break

        if re.search(r"AKIA[0-9A-Z]{16}", text):
            findings.append(
                RawFinding(
                    rule_id="AWS_ACCESS_KEY_LITERAL",
                    severity="critical",
                    resource_type=None,
                    resource_name=None,
                    title="Possible AWS access key material in Terraform",
                    description="A string matching AKIA* access key format was found.",
                    remediation="Rotate the key immediately and load credentials via OIDC/IRSA or environment injection.",
                    terraform_fix_example="# Remove static keys; use IAM roles for workloads",
                    file_path=path,
                )
            )

    # Duplicate suppression for identical S3 rule on same bucket - acceptable for MVP

    return findings


def collect_cloudformation_findings(
    parsed_files: Iterable[tuple[str, dict[str, Any]]],
    raw_text_by_path: dict[str, str],
) -> list[RawFinding]:
    findings: list[RawFinding] = []
    docs = list(parsed_files)
    resources: list[tuple[str, str, str, dict[str, Any]]] = []

    for path, doc in docs:
        for logical_id, resource in (doc.get("Resources") or {}).items():
            if not isinstance(resource, dict):
                continue
            resource_type = str(resource.get("Type", ""))
            props = resource.get("Properties") or {}
            if isinstance(props, dict):
                resources.append((path, logical_id, resource_type, props))

    for path, logical_id, resource_type, props in resources:
        if resource_type == "AWS::S3::Bucket":
            access_control = str(props.get("AccessControl", "")).lower()
            if access_control in {"publicread", "publicreadwrite"}:
                findings.append(
                    RawFinding(
                        rule_id="CFN_S3_PUBLIC_ACL",
                        severity="critical",
                        resource_type=resource_type,
                        resource_name=logical_id,
                        title="CloudFormation S3 bucket uses a public ACL",
                        description=f"{logical_id} sets AccessControl to {props.get('AccessControl')!r}.",
                        remediation="Remove public ACLs and enforce S3 Block Public Access.",
                        terraform_fix_example="AccessControl: Private",
                        file_path=path,
                    )
                )
            pab = props.get("PublicAccessBlockConfiguration") or {}
            if isinstance(pab, dict) and any(_boolish(pab.get(k)) is False for k in ("BlockPublicAcls", "BlockPublicPolicy")):
                findings.append(
                    RawFinding(
                        rule_id="CFN_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
                        severity="high",
                        resource_type=resource_type,
                        resource_name=logical_id,
                        title="CloudFormation S3 public access block is disabled",
                        description="BlockPublicAcls or BlockPublicPolicy is false.",
                        remediation="Set all S3 public access block options to true.",
                        terraform_fix_example="PublicAccessBlockConfiguration:\n  BlockPublicAcls: true\n  BlockPublicPolicy: true",
                        file_path=path,
                    )
                )

        if resource_type == "AWS::EC2::SecurityGroup":
            ingress = props.get("SecurityGroupIngress") or []
            if isinstance(ingress, dict):
                ingress = [ingress]
            for rule in ingress if isinstance(ingress, list) else []:
                if not isinstance(rule, dict):
                    continue
                if not _cidr_open_to_world(rule.get("CidrIp") or rule.get("CidrIpv6")):
                    continue
                try:
                    from_port = int(rule.get("FromPort", 0))
                    to_port = int(rule.get("ToPort", 0))
                except (TypeError, ValueError):
                    continue
                protocol = str(rule.get("IpProtocol", "tcp")).lower()
                if protocol in {"-1", "all"}:
                    findings.append(
                        RawFinding(
                            rule_id="CFN_SG_ALL_TRAFFIC_OPEN",
                            severity="critical",
                            resource_type=resource_type,
                            resource_name=logical_id,
                            title="CloudFormation security group allows all traffic from the internet",
                            description="SecurityGroupIngress permits all protocols from an internet CIDR.",
                            remediation="Restrict protocol, ports, and CIDRs to the minimum required.",
                            terraform_fix_example="# Replace 0.0.0.0/0 with trusted CIDRs",
                            file_path=path,
                        )
                    )
                if protocol in {"tcp", "-1", "all"} and from_port <= 22 <= to_port:
                    findings.append(
                        RawFinding(
                            rule_id="CFN_SG_OPEN_SSH",
                            severity="critical",
                            resource_type=resource_type,
                            resource_name=logical_id,
                            title="CloudFormation security group allows SSH from the internet",
                            description="SecurityGroupIngress permits port 22 from 0.0.0.0/0 or ::/0.",
                            remediation="Use VPN, bastion restrictions, or SSM Session Manager instead of open SSH.",
                            terraform_fix_example="CidrIp: 10.0.0.0/8",
                            file_path=path,
                        )
                    )

        if resource_type == "AWS::RDS::DBInstance":
            if _boolish(props.get("PubliclyAccessible")):
                findings.append(
                    RawFinding(
                        rule_id="CFN_RDS_PUBLIC",
                        severity="critical",
                        resource_type=resource_type,
                        resource_name=logical_id,
                        title="CloudFormation RDS instance is publicly accessible",
                        description="PubliclyAccessible is true.",
                        remediation="Place RDS in private subnets and disable public access.",
                        terraform_fix_example="PubliclyAccessible: false",
                        file_path=path,
                    )
                )
            if _boolish(props.get("StorageEncrypted")) is False:
                findings.append(
                    RawFinding(
                        rule_id="CFN_RDS_UNENCRYPTED",
                        severity="high",
                        resource_type=resource_type,
                        resource_name=logical_id,
                        title="CloudFormation RDS storage encryption disabled",
                        description="StorageEncrypted is false.",
                        remediation="Enable storage encryption with KMS.",
                        terraform_fix_example="StorageEncrypted: true",
                        file_path=path,
                    )
                )

        if resource_type in {"AWS::IAM::Policy", "AWS::IAM::ManagedPolicy"}:
            policy = json.dumps(props.get("PolicyDocument") or {})
            if '"Action": "*"' in policy or '"Action":["*"]' in policy.replace(" ", ""):
                findings.append(
                    RawFinding(
                        rule_id="CFN_IAM_WILDCARD_ACTION",
                        severity="critical",
                        resource_type=resource_type,
                        resource_name=logical_id,
                        title="CloudFormation IAM policy grants Action=*",
                        description="Wildcard actions grant broad API access.",
                        remediation="Replace wildcard actions with least-privilege action lists.",
                        terraform_fix_example="Action:\n  - s3:GetObject",
                        file_path=path,
                    )
                )
            if '"Resource": "*"' in policy or '"Resource":["*"]' in policy.replace(" ", ""):
                findings.append(
                    RawFinding(
                        rule_id="CFN_IAM_WILDCARD_RESOURCE",
                        severity="high",
                        resource_type=resource_type,
                        resource_name=logical_id,
                        title="CloudFormation IAM policy grants Resource=*",
                        description="Wildcard resources are overly permissive.",
                        remediation="Scope resources to ARNs or prefixes.",
                        terraform_fix_example="Resource: arn:aws:s3:::example-bucket/*",
                        file_path=path,
                    )
                )

    has_trail = any(resource_type == "AWS::CloudTrail::Trail" for _, _, resource_type, _ in resources)
    if docs and not has_trail:
        findings.append(
            RawFinding(
                rule_id="CFN_CLOUDTRAIL_MISSING",
                severity="medium",
                resource_type="AWS::CloudTrail::Trail",
                resource_name="*",
                title="No CloudFormation CloudTrail resource detected",
                description="Template did not declare CloudTrail; governance and forensic coverage may be incomplete.",
                remediation="Add an organization or account trail with log file validation.",
                terraform_fix_example="Type: AWS::CloudTrail::Trail",
                file_path=docs[0][0],
            )
        )

    for path, text in raw_text_by_path.items():
        for rule_id, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(
                    RawFinding(
                        rule_id=f"CFN_{rule_id.upper()}",
                        severity="critical",
                        resource_type=None,
                        resource_name=None,
                        title="Potential hardcoded secret in CloudFormation",
                        description="A literal assignment resembling a password/secret was detected.",
                        remediation="Use Secrets Manager, SSM Parameter Store, or dynamic references.",
                        terraform_fix_example="{{resolve:secretsmanager:secret-id:SecretString:password}}",
                        file_path=path,
                    )
                )
                break

    return findings


def summarize_severities(findings: Iterable[RawFinding]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in findings:
        counts[item.severity] = counts.get(item.severity, 0) + 1
    return counts


def compute_risk_scores(findings: list[RawFinding]) -> tuple[float, float, dict[str, Any]]:
    weights = {"critical": 10, "high": 7, "medium": 5, "low": 2}
    points = sum(weights.get(f.severity, 0) for f in findings)
    # Normalize: 40 weighted points maps to 100 risk score (tunable)
    risk_score = min(100.0, (points / 40.0) * 100.0) if points else 0.0
    compliance_percent = max(0.0, min(100.0, 100.0 - risk_score))
    summary = {
        "severity_counts": summarize_severities(findings),
        "weighted_points": points,
        "risk_score": risk_score,
        "compliance_percent": compliance_percent,
    }
    return risk_score, compliance_percent, summary
