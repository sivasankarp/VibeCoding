from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.scan import Scan, ScanStatus
from app.schemas.guardrail import MetricsResponse, MetricsSeverity, TrendPoint


def get_metrics(db: Session) -> MetricsResponse:
    total_scans = int(db.scalar(select(func.count()).select_from(Scan)) or 0)
    completed = int(
        db.scalar(select(func.count()).select_from(Scan).where(Scan.status == ScanStatus.completed.value)) or 0
    )
    total_findings = int(db.scalar(select(func.count()).select_from(Finding)) or 0)
    critical_findings = int(
        db.scalar(
            select(func.count()).select_from(Finding).where(Finding.severity == "critical"),
        )
        or 0
    )

    avg_risk = db.scalar(
        select(func.avg(Scan.risk_score)).where(
            Scan.status == ScanStatus.completed.value,
            Scan.risk_score.is_not(None),
        )
    )
    avg_risk_f = float(avg_risk or 0.0)

    avg_comp = db.scalar(
        select(func.avg(Scan.compliance_percent)).where(
            Scan.status == ScanStatus.completed.value,
            Scan.compliance_percent.is_not(None),
        )
    )
    avg_comp_f = float(avg_comp or 0.0)

    sev_rows = db.execute(
        select(Finding.severity, func.count())
        .group_by(Finding.severity)
    ).all()
    dist = MetricsSeverity()
    for sev, cnt in sev_rows:
        if sev == "critical":
            dist.critical = int(cnt)
        elif sev == "high":
            dist.high = int(cnt)
        elif sev == "medium":
            dist.medium = int(cnt)
        elif sev == "low":
            dist.low = int(cnt)

    trend_rows = db.execute(
        select(Scan.id, Scan.risk_score, Scan.created_at)
        .where(Scan.status == ScanStatus.completed.value)
        .order_by(Scan.created_at.asc())
        .limit(50)
    ).all()
    trend = [
        TrendPoint(scan_id=row[0], risk_score=float(row[1]) if row[1] is not None else None, created_at=row[2])
        for row in trend_rows
    ]

    return MetricsResponse(
        total_scans=total_scans,
        completed_scans=completed,
        total_findings=total_findings,
        critical_findings=critical_findings,
        average_risk_score=round(avg_risk_f, 2),
        average_compliance_percent=round(avg_comp_f, 2),
        severity_distribution=dist,
        risk_trend=trend[-20:] if len(trend) > 20 else trend,
    )


def dashboard_context(db: Session) -> dict[str, object]:
    metrics = get_metrics(db)
    recent = (
        db.execute(select(Finding).order_by(Finding.created_at.desc()).limit(30)).scalars().all()
    )
    return {
        "metrics": metrics.model_dump(mode="json"),
        "metrics_json": json.dumps(metrics.model_dump(mode="json"), default=str),
        "recent_findings": recent,
    }
