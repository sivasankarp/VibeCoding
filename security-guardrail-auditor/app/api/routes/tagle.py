from fastapi import APIRouter, HTTPException

from app.integrations.tagle import TAGLE_OFFICIAL_BASE, TAGLE_OFFICIAL_QUIZ, load_assessment
from app.integrations.tagle.schemas import TagleAssessment

router = APIRouter(prefix="/tagle", tags=["tagle"])


@router.get("/assessment", response_model=TagleAssessment)
def get_assessment() -> TagleAssessment:
    """Return the configured Tagle-style assessment (bundled sample unless overridden)."""
    try:
        return load_assessment()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/about")
def tagle_about() -> dict[str, str | list[str]]:
    """Pointers to Tagle.ai and how this repo integrates without an official PyPI wheel."""
    return {
        "vendor": "Tagle.ai",
        "official_site": TAGLE_OFFICIAL_BASE,
        "official_quiz": TAGLE_OFFICIAL_QUIZ,
        "integration_notes": (
            "This codebase ships an in-repo integration module (app.integrations.tagle) "
            "plus a bundled JSON sample under data/. There is no official pip package named "
            "tagle on PyPI; set TAGLE_ASSESSMENT_JSON to point at your own export if you "
            "capture results externally."
        ),
        "sample_files": [
            "data/tagle_assessment.sample.json",
            "data/TAGLE_AI_TEST_RESULTS.md",
        ],
    }
