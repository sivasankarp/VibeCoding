# Team share URLs

Run the app locally first:

```bash
cd security-guardrail-auditor
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Share these URLs with the review team during the demo:

| Label | URL | Purpose |
| --- | --- | --- |
| Security dashboard | http://127.0.0.1:8000/ | Visual risk score, charts, and recent findings |
| Swagger API docs | http://127.0.0.1:8000/docs | Upload Terraform files and inspect API contracts |
| Health check | http://127.0.0.1:8000/health | Confirm the app is running |
| Metrics JSON | http://127.0.0.1:8000/metrics | Machine-readable dashboard metrics |
| Tagle report | http://127.0.0.1:8000/tagle/report | Browser-friendly Tagle-style dashboard report |
| Tagle JSON | http://127.0.0.1:8000/tagle/assessment | Machine-readable Tagle assessment payload |
| Submission URL list | http://127.0.0.1:8000/submission/urls | JSON copy of this share list |
| GitHub repository | https://github.com/sivasankarp/VibeCoding | Final source code repository |

Final submission note: this local-first MVP does not provision cloud resources, so there are no cloud resources to decommission.
