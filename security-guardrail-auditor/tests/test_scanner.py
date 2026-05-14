from pathlib import Path

from app.scanners.engine import collect_raw_findings, compute_risk_scores
from app.scanners.hcl_parser import parse_hcl_string


def test_insecure_fixture_triggers_multiple_rules() -> None:
    p = Path(__file__).resolve().parent / "fixtures" / "terraform" / "insecure.tf"
    text = p.read_text(encoding="utf-8")
    doc = parse_hcl_string(text, "insecure.tf")
    findings = collect_raw_findings([("insecure.tf", doc)], {"insecure.tf": text})
    rule_ids = {f.rule_id for f in findings}
    assert "S3_PUBLIC_ACL" in rule_ids
    assert "SG_OPEN_SSH" in rule_ids
    assert "RDS_PUBLIC" in rule_ids
    assert "RDS_UNENCRYPTED" in rule_ids
    assert "EC2_PUBLIC_IP" in rule_ids
    assert "EBS_UNENCRYPTED" in rule_ids
    assert "IAM_WILDCARD_ACTION" in rule_ids
    assert "IAM_WILDCARD_RESOURCE" in rule_ids
    assert "CLOUDTRAIL_MISSING" in rule_ids
    risk, comp, summary = compute_risk_scores(findings)
    assert risk >= 0
    assert comp <= 100
    assert summary["severity_counts"]["critical"] >= 1


def test_clean_minimal_has_cloudtrail_gap_only() -> None:
    text = """
resource "aws_s3_bucket" "private" {
  bucket = "ok"
  acl    = "private"
}
"""
    doc = parse_hcl_string(text, "ok.tf")
    findings = collect_raw_findings([("ok.tf", doc)], {"ok.tf": text})
    assert any(f.rule_id == "CLOUDTRAIL_MISSING" for f in findings)


def test_password_literal_detected_in_raw_text() -> None:
    text = 'resource "null_resource" "demo" {\n  password = "SuperBad123"\n}\n'
    doc = parse_hcl_string(text, "pw.tf")
    findings = collect_raw_findings([("pw.tf", doc)], {"pw.tf": text})
    assert any(f.rule_id == "HARDCODED_PASSWORD" for f in findings)
