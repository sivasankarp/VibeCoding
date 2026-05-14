from pathlib import Path

from app.main import app
from fastapi.testclient import TestClient


def test_scan_metrics_findings_flow() -> None:
    client = TestClient(app)
    tf_path = Path(__file__).resolve().parent / "fixtures" / "terraform" / "insecure.tf"
    files = [("files", ("insecure.tf", tf_path.read_bytes(), "application/octet-stream"))]
    data = {"name": "pytest-scan"}
    r = client.post("/scan", data=data, files=files)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["scan"]["status"] in {"completed", "failed"}
    if body["scan"]["status"] == "completed":
        assert body["scan"]["risk_score"] is not None

    scans = client.get("/scans")
    assert scans.status_code == 200
    assert len(scans.json()) >= 1

    m = client.get("/metrics")
    assert m.status_code == 200
    mj = m.json()
    assert "total_findings" in mj

    findings = client.get("/findings", params={"limit": 200})
    assert findings.status_code == 200
    items = findings.json()
    assert isinstance(items, list)
    if items:
        fid = items[0]["id"]
        one = client.get(f"/findings/{fid}")
        assert one.status_code == 200

    sid = body["scan"]["id"]
    dr = client.delete(f"/scan/{sid}")
    assert dr.status_code == 204


def test_scan_requires_tf() -> None:
    client = TestClient(app)
    r = client.post("/scan", data={"name": "bad"}, files={"files": ("readme.txt", b"hello", "text/plain")})
    assert r.status_code == 400
