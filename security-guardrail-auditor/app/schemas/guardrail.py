from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    rule_id: str
    severity: str
    resource_type: str | None
    resource_name: str | None
    title: str
    description: str | None
    remediation: str | None
    terraform_fix_example: str | None
    file_path: str | None
    line_number: int | None
    created_at: datetime


class ScanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    status: str
    risk_score: float | None
    compliance_percent: float | None
    summary_json: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ScanDetailRead(ScanRead):
    finding_count: int = 0


class ScanCreateResponse(BaseModel):
    scan: ScanRead
    message: str = "Scan completed"


class MetricsSeverity(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class TrendPoint(BaseModel):
    scan_id: int
    risk_score: float | None
    created_at: datetime


class MetricsResponse(BaseModel):
    total_scans: int
    completed_scans: int
    total_findings: int
    critical_findings: int
    average_risk_score: float
    average_compliance_percent: float
    severity_distribution: MetricsSeverity
    risk_trend: list[TrendPoint]
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
