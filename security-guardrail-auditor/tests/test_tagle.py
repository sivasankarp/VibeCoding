from pathlib import Path

from app.integrations.tagle.loader import load_assessment
from app.integrations.tagle.schemas import TagleAssessment
from app.main import app
from fastapi.testclient import TestClient


def test_load_bundled_sample_assessment() -> None:
    assessment = load_assessment()
    assert isinstance(assessment, TagleAssessment)
    assert assessment.archetype == "architect"
    assert assessment.maturity.stage_number == 9
    assert 0 <= assessment.tagle_score <= 100
    assert len(assessment.dimensions) == 5


def test_load_explicit_path() -> None:
    sample = Path(__file__).resolve().parents[1] / "data" / "tagle_assessment.sample.json"
    assessment = load_assessment(sample)
    assert assessment.source == "bundled_sample"


def test_tagle_http_endpoints() -> None:
    client = TestClient(app)
    r = client.get("/tagle/assessment")
    assert r.status_code == 200
    body = r.json()
    assert body["archetype"] == "architect"
    about = client.get("/tagle/about")
    assert about.status_code == 200
    assert "official_quiz" in about.json()

    report = client.get("/tagle/report")
    assert report.status_code == 200
    assert "Tagle.ai-style report" in report.text
    assert "Architect profile" in report.text


def test_submission_urls_endpoint() -> None:
    client = TestClient(app)
    r = client.get("/submission/urls")
    assert r.status_code == 200
    body = r.json()
    labels = {item["label"] for item in body["team_share_urls"]}
    assert "Security dashboard" in labels
    assert "Tagle report" in labels
    assert body["github_repository"].startswith("https://github.com/")
