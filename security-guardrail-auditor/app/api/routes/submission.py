from fastapi import APIRouter

router = APIRouter(prefix="/submission", tags=["submission"])


@router.get("/urls")
def submission_urls() -> dict[str, object]:
    """Return the URLs a reviewer/team member should open during the demo."""
    base = "http://127.0.0.1:8000"
    github = "https://github.com/sivasankarp/VibeCoding"
    return {
        "local_base_url": base,
        "github_repository": github,
        "team_share_urls": [
            {"label": "Security dashboard", "url": f"{base}/", "purpose": "Visual risk score, charts, recent findings"},
            {"label": "Swagger API Docs", "url": f"{base}/docs", "purpose": "Run scans and inspect API contracts"},
            {"label": "Health Check", "url": f"{base}/health", "purpose": "Confirm the app is running"},
            {"label": "Metrics JSON", "url": f"{base}/metrics", "purpose": "Machine-readable dashboard metrics"},
            {"label": "Tagle report", "url": f"{base}/tagle/report", "purpose": "Reviewer-friendly Tagle-style dashboard report"},
            {"label": "Tagle JSON", "url": f"{base}/tagle/assessment", "purpose": "Machine-readable Tagle assessment payload"},
            {"label": "Submission URLs JSON", "url": f"{base}/submission/urls", "purpose": "This share list"},
            {"label": "GitHub Repository", "url": github, "purpose": "Final source code repository"},
        ],
        "submission_notes": [
            "Replace the bundled Tagle sample with your real Tagle.ai result before final submission.",
            "No cloud resources are provisioned by this local-first MVP, so there are no cloud resources to decommission.",
        ],
    }
