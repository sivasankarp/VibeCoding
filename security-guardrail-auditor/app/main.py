from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import __version__
from app.api.routes import guardrail, health, submission, tagle
from app.core.config import PROJECT_ROOT, settings
from app.core.database import get_db, init_db
from app.services import metrics_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.include_router(health.router)
    application.include_router(guardrail.router)
    application.include_router(tagle.router)
    application.include_router(submission.router)

    static_dir = Path(__file__).parent / "static"
    application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @application.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
        ctx = metrics_service.dashboard_context(db)
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {"app_name": settings.app_name, **ctx},
        )

    return application


app = create_app()
