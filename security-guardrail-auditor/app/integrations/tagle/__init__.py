"""
Tagle.ai integration (in-repo).

Tagle.ai is a web-based AI readiness assessment (see https://tagle.ai). There is no
official ``pip install tagle`` package on PyPI at the time of integration; this package
provides typed models, JSON loading, and HTTP exposure for bundled or file-supplied results.
"""

from app.integrations.tagle.loader import load_assessment
from app.integrations.tagle.schemas import TagleAssessment

TAGLE_OFFICIAL_BASE = "https://tagle.ai"
TAGLE_OFFICIAL_QUIZ = "https://tagle.ai/quiz"

__all__ = [
    "TAGLE_OFFICIAL_BASE",
    "TAGLE_OFFICIAL_QUIZ",
    "TagleAssessment",
    "load_assessment",
]
