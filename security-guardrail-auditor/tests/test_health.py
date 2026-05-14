import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_root_renders_dashboard_stub(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Security posture" in response.text
