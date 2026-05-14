from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import hcl2


def parse_hcl_string(source: str, filename: str = "inline.tf") -> dict[str, Any]:
    """Parse Terraform HCL from a string. Raises on syntax errors."""
    return hcl2.load(io.StringIO(source))


def parse_hcl_path(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return hcl2.load(handle)


def ensure_tf_suffix(path: Path) -> None:
    if path.suffix.lower() not in {".tf", ".tfvars"}:
        raise ValueError(f"Unsupported file type for scan: {path}")
