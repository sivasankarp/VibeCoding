# Portfolio deliverables — Enterprise Security Guardrail Auditor

Use this document for demos, interviews, and slide decks. Adapt wording to your own experience.

---

## 1. Slide deck outline (10–12 slides)

1. **Title** — Enterprise Security Guardrail Auditor; your name; “Terraform + FastAPI + SQLite”.
2. **Problem** — IaC drifts into public buckets, open SGs, weak IAM; reviews are slow and inconsistent.
3. **Solution** — Automated upload → parse (`python-hcl2`) → rule engine → risk score → persisted history.
4. **Architecture** — Diagram: Browser / API / Scanner / SQLite; call out local-first, no cloud billing.
5. **Rule engine** — Table of categories (S3, SG, RDS, IAM, secrets, logging).
6. **Risk scoring** — Weights; compliance %; why normalization matters.
7. **Live demo flow** — Swagger `POST /scan` → dashboard refresh → charts update.
8. **Dashboard** — Dark UI, Chart.js severity + trend; findings table.
9. **Quality** — Pytest (scanner + API), Ruff in CI, Docker packaging.
10. **Security & ethics** — Secrets in fixtures are synthetic; scanner flags literals; no external data exfil.
11. **Roadmap** — OPA integration, SARIF export, OIDC auth, Postgres for multi-tenant.
12. **Q&A** — Thank you / contact.

---

## 2. Resume-ready project summary (short)

**Enterprise Security Guardrail Auditor** — Built an API-first Terraform auditing service in Python (FastAPI, SQLAlchemy, SQLite) with a `python-hcl2` parser, extensible static analysis rules for cloud misconfigurations (S3 exposure, open security groups, weak IAM, encryption gaps), weighted risk scoring, persisted scan history, Chart.js dashboard, Docker deployment, and GitHub Actions (Ruff + pytest). Demonstrates secure SDLC thinking, testable rule design, and pragmatic MVP delivery.

---

## 3. Interview talking points

- **Why SQLite first?** Zero-ops local MVP; swap connection string for Postgres in production.
- **How do you avoid false positives?** Rules are conservative heuristics; production would add suppressions, resource graph, and OPA/conftest for policy-as-code.
- **How would you scale parsing?** Queue scans (Celery/RQ), object storage for uploads, shard by tenant.
- **Secrets in Terraform** — Never commit; use CI secret scanning + vault; tool flags literals for review.
- **Extensibility** — `RawFinding` + rule IDs map cleanly to compliance frameworks (CIS-style mapping as a next step).

---

## 4. Demo walkthrough (2 minutes)

1. `uvicorn app.main:app --reload`
2. Open `/` — explain cards and empty state vs populated state.
3. Open `/docs` — `POST /scan` with `tests/fixtures/terraform/insecure.tf`.
4. Reload `/` — charts and table populate; mention `GET /metrics` JSON for integrations.

---

## 5. Future enhancements (backlog)

- OPA/Rego or Checkov-style policy packs  
- GitHub App for PR comments  
- SARIF export for GitHub Advanced Security  
- Multi-file module graphs and `.tfvars` risk  
- RBAC + API keys for shared deployments  
