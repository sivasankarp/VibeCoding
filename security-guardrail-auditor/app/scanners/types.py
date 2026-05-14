from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Severity = Literal["critical", "high", "medium", "low"]


class RawFinding(BaseModel):
    """Security finding before persistence."""

    rule_id: str
    severity: Severity
    resource_type: str | None = None
    resource_name: str | None = None
    title: str
    description: str
    remediation: str
    terraform_fix_example: str
    file_path: str | None = None
    line_number: int | None = None
