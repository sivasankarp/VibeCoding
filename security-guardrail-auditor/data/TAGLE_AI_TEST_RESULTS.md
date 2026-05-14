# Tagle.ai test results (engineering record)

This file documents **automated checks** run in this repository for the Tagle.ai integration, plus the **bundled sample assessment** that mirrors public Tagle.ai vocabulary (archetypes and the twelve-stage maturity spectrum described on [tagle.ai](https://tagle.ai)).

## Important distinction

- **Live Tagle.ai quiz:** The product experience runs on Tagle’s website ([Take the Quiz](https://tagle.ai/quiz)). This repo does **not** call private Tagle APIs.
- **What we ship:** An in-repo Python module (`app.integrations.tagle`), a **validated JSON sample** (`data/tagle_assessment.sample.json`), and REST endpoints (`GET /tagle/assessment`, `GET /tagle/about`).

The bundled JSON is **not** a personal psychological result from Tagle servers; it is a **demo payload** so engineers can wire dashboards, persistence, or CI without credentials.

## Automated test matrix (this codebase)

| Check | Command | Result (latest run) |
|-------|---------|---------------------|
| Schema + loader | `pytest tests/test_tagle.py` | Validates `data/tagle_assessment.sample.json` against `TagleAssessment` |
| HTTP contract | `TestClient` against `GET /tagle/assessment` | Returns `200` with the same structured payload |
| About metadata | `GET /tagle/about` | Returns official URLs + integration notes |

Run locally:

```bash
cd security-guardrail-auditor
source .venv/bin/activate  # after pip install -r requirements.txt
pytest tests/test_tagle.py -q
```

## Bundled sample outcome (illustrative)

| Field | Value |
|-------|--------|
| Archetype | **Architect** |
| Maturity stage | **9 / 12 — Confident Operator** (Confident mindset × Operator skills) |
| Tagle-style score | **78.5 / 100** |
| Source | `bundled_sample` (`data/tagle_assessment.sample.json`) |

Dimension scores and action-plan bullets are listed in that JSON file for machine-readable reuse.

## Replacing the sample with your own results

1. Complete the official flow on [tagle.ai](https://tagle.ai) (or export from any internal pipeline you are authorized to use).
2. Map your export fields onto the schema in `app/integrations/tagle/schemas.py` (or adjust the schema if your export differs).
3. Point `TAGLE_ASSESSMENT_JSON` in `.env` at your JSON file and restart Uvicorn.
