from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.integrations.tagle import TAGLE_OFFICIAL_BASE, TAGLE_OFFICIAL_QUIZ, load_assessment
from app.integrations.tagle.schemas import TagleAssessment

router = APIRouter(prefix="/tagle", tags=["tagle"])
templates = Jinja2Templates(directory=str(Path(__file__).parents[2] / "templates"))


@router.get("/assessment", response_model=TagleAssessment)
def get_assessment() -> TagleAssessment:
    """Return the configured Tagle-style assessment (bundled sample unless overridden)."""
    try:
        return load_assessment()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/report", response_class=HTMLResponse)
def tagle_report(request: Request) -> HTMLResponse:
    """Render a Tagle-style dashboard report for demos and submission review."""
    assessment = get_assessment()
    sorted_dimensions = sorted(assessment.dimensions, key=lambda item: item.score, reverse=True)
    score_band = "Ready"
    if assessment.tagle_score < 60:
        score_band = "Developing"
    elif assessment.tagle_score >= 80:
        score_band = "Strong"

    return templates.TemplateResponse(
        request,
        "tagle_report.html",
        {
            "assessment": assessment,
            "score_band": score_band,
            "top_dimensions": sorted_dimensions[:2],
            "growth_dimensions": sorted_dimensions[-2:],
            "official_quiz": TAGLE_OFFICIAL_QUIZ,
        },
    )


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
