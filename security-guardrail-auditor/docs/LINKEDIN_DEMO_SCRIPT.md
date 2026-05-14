# 60-second LinkedIn demo script

## Video title

Enterprise Security Guardrail Auditor — Python, FastAPI, DevSecOps

## Recording flow

1. Start at the dashboard: `http://127.0.0.1:8000/`
2. Show the risk score, severity chart, trend chart, and recent findings table.
3. Open Swagger: `http://127.0.0.1:8000/docs`
4. Show `POST /scan` and mention Terraform + CloudFormation upload support.
5. Return to the dashboard and explain that findings are persisted in SQLite.
6. Open the Tagle-style report: `http://127.0.0.1:8000/tagle/report`
7. End on GitHub repository view.

## Voiceover

Hi, I’m Siva. I built an Enterprise Security Guardrail Auditor as a Python API-first DevSecOps project.

It scans Terraform and CloudFormation files before deployment and detects risky cloud patterns like public S3 buckets, open SSH, public RDS, weak IAM policies, missing CloudTrail, encryption gaps, and hardcoded secrets.

The backend is built with FastAPI, SQLAlchemy, and SQLite. The scanner calculates a weighted risk score and exposes the results through REST APIs and Swagger docs.

I also built a visual dashboard with risk scoring, severity distribution, trend tracking, and recent findings, plus a Tagle-style report page for the challenge submission.

The project includes Docker support, GitHub Actions CI, Ruff linting, and pytest coverage.

This helped me practice cloud security, platform engineering, API design, testing, and AI-assisted development in one complete project.

## LinkedIn caption

I built an Enterprise Security Guardrail Auditor using Python, FastAPI, SQLite, Terraform/CloudFormation parsing, and a visual risk dashboard.

The tool scans infrastructure-as-code files for risky patterns such as public S3 buckets, open SSH, public RDS, weak IAM policies, missing CloudTrail, encryption gaps, and hardcoded secrets.

Tech stack: Python, FastAPI, SQLAlchemy, SQLite, Jinja2, Tailwind CSS, Chart.js, Docker, Pytest, Ruff, GitHub Actions.

This project helped me think beyond writing code and focus on architecture, security, API contracts, testability, and DevSecOps workflows.

GitHub: https://github.com/sivasankarp/VibeCoding
