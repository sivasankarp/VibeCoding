from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.core.config import PROJECT_ROOT, settings
from app.integrations.tagle.schemas import TagleAssessment

_DEFAULT_SAMPLE = PROJECT_ROOT / "data" / "tagle_assessment.sample.json"


def resolve_assessment_path() -> Path:
    """Prefer explicit env path; otherwise bundled sample under data/."""
    if settings.tagle_assessment_json_path is not None:
        return Path(settings.tagle_assessment_json_path)
    return _DEFAULT_SAMPLE


def load_assessment(path: Path | None = None) -> TagleAssessment:
    """Load and validate a Tagle-style assessment JSON file."""
    target = path or resolve_assessment_path()
    if not target.is_file():
        raise FileNotFoundError(f"Tagle assessment JSON not found: {target}")
    raw = json.loads(target.read_text(encoding="utf-8"))
    try:
        return TagleAssessment.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid Tagle assessment JSON at {target}") from exc
