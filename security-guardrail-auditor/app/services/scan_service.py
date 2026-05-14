from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.finding import Finding
from app.models.scan import Scan, ScanStatus
from app.models.uploaded_file import UploadedFile
from app.scanners.cfn_parser import parse_cfn_string
from app.scanners.engine import (
    collect_cloudformation_findings,
    collect_raw_findings,
    compute_risk_scores,
)
from app.scanners.hcl_parser import parse_hcl_string


def run_scan_from_text_files(db: Session, scan_name: str | None, files: list[tuple[str, str]]) -> Scan:
    """
    Persist a scan, store uploads, parse .tf files, run the rule engine, and save findings.

    ``files`` is a list of (logical_filename, utf-8 text).
    """
    supported_suffixes = (".tf", ".json", ".yaml", ".yml")
    if not any(name.lower().endswith(supported_suffixes) for name, _ in files):
        raise ValueError("At least one Terraform (.tf) or CloudFormation (.json/.yaml/.yml) file is required.")

    scan = Scan(name=scan_name, status=ScanStatus.processing.value)
    db.add(scan)
    db.flush()

    scan_dir = Path(settings.upload_dir) / str(scan.id)
    scan_dir.mkdir(parents=True, exist_ok=True)

    db.add(
        AuditLog(
            scan_id=scan.id,
            action="scan_started",
            details=json.dumps({"files": [name for name, _ in files]}),
        )
    )
    db.flush()

    parsed_tf: list[tuple[str, dict]] = []
    parsed_cfn: list[tuple[str, dict]] = []
    raw_tf_by_path: dict[str, str] = {}
    raw_cfn_by_path: dict[str, str] = {}

    try:
        for logical_name, text in files:
            safe_name = Path(logical_name).name
            if not safe_name or safe_name in {".", ".."}:
                safe_name = "upload.tf"
            dest = scan_dir / safe_name
            dest.write_text(text, encoding="utf-8")
            db.add(
                UploadedFile(
                    scan_id=scan.id,
                    original_filename=logical_name,
                    stored_path=str(dest),
                    size_bytes=len(text.encode("utf-8")),
                )
            )

            lower_name = logical_name.lower()
            if not lower_name.endswith(supported_suffixes):
                continue

            if lower_name.endswith(".tf"):
                raw_tf_by_path[logical_name] = text
                parsed_doc = parse_hcl_string(text, logical_name)
                parsed_tf.append((logical_name, parsed_doc))
            else:
                raw_cfn_by_path[logical_name] = text
                parsed_doc = parse_cfn_string(text, logical_name)
                parsed_cfn.append((logical_name, parsed_doc))

        raw_findings = collect_raw_findings(parsed_tf, raw_tf_by_path)
        raw_findings.extend(collect_cloudformation_findings(parsed_cfn, raw_cfn_by_path))
        risk_score, compliance, summary = compute_risk_scores(raw_findings)

        for rf in raw_findings:
            db.add(
                Finding(
                    scan_id=scan.id,
                    rule_id=rf.rule_id,
                    severity=rf.severity,
                    resource_type=rf.resource_type,
                    resource_name=rf.resource_name,
                    title=rf.title[:512],
                    description=rf.description,
                    remediation=rf.remediation,
                    terraform_fix_example=rf.terraform_fix_example,
                    file_path=rf.file_path,
                    line_number=rf.line_number,
                )
            )

        scan.status = ScanStatus.completed.value
        scan.risk_score = risk_score
        scan.compliance_percent = compliance
        scan.summary_json = json.dumps(summary)
        db.add(
            AuditLog(
                scan_id=scan.id,
                action="scan_completed",
                details=json.dumps({"finding_count": len(raw_findings)}),
            )
        )
    except Exception as exc:  # noqa: BLE001 — surface as failed scan
        scan.status = ScanStatus.failed.value
        scan.error_message = str(exc)[:4096]
        db.add(AuditLog(scan_id=scan.id, action="scan_failed", details=str(exc)[:4096]))

    db.commit()
    db.refresh(scan)
    return scan


def delete_scan(db: Session, scan_id: int) -> bool:
    scan = db.get(Scan, scan_id)
    if scan is None:
        return False
    db.delete(scan)
    db.commit()
    return True
