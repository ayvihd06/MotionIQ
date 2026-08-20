from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

def test_upload_invalid_extension():
    files = {"file": ("test.txt", b"invalid content", "text/plain")}
    response = client.post("/api/videos/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
