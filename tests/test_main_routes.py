from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_api_v1_root_does_not_advertise_generic_ai_route():
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert "ai" not in response.json()["endpoints"]


def test_generic_ai_placeholder_route_is_removed():
    response = client.get("/api/v1/ai")

    assert response.status_code == 404
