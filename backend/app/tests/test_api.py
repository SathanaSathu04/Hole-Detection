import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"


def test_system_status(client):
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "system" in data
    assert "machine" in data
    assert "camera" in data


def test_machine_endpoints(client):
    res = client.get("/api/machine/status")
    assert res.status_code == 200
    assert res.json()["mode"] == "SIMULATION"

    res = client.get("/api/machine/position")
    assert res.status_code == 200
    assert "x" in res.json()


def test_camera_endpoints(client):
    res = client.get("/api/camera/status")
    assert res.status_code == 200

    res = client.get("/api/camera/frame")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
