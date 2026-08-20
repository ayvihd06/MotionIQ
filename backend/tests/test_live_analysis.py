import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_save_live_analysis_unauthenticated():
    payload = {
        "cadence_spm": 172.0,
        "step_count": 28,
        "left_right_symmetry_pct": 93.5,
        "trunk_lean_deg": 8.2,
        "duration_sec": 20.0,
        "camera_view": "Side view",
        "camera_suitability": "Good",
        "tracking_quality_pct": 88.0,
        "form_classification": "Live Observational Running Form (172 SPM)",
        "overall_confidence": "Medium",
        "observations": ["Stable sagittal tracking"]
    }
    
    response = client.post("/api/analyses/live", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "analysis_id" in data
    assert data["cadence_spm"] == 172.0
    assert data["left_right_symmetry_pct"] == 93.5
    assert data["trunk_lean_deg"] == 8.2
    assert data["status"] == "completed"
    assert data["overall_confidence"] == "Medium"

def test_save_live_analysis_authenticated_isolation():
    # Register test runner
    email = "live_runner_test@motioniq.com"
    pwd = "SecurePassword123!"
    reg_res = client.post("/api/auth/register", json={"email": email, "password": pwd, "display_name": "Live Runner"})
    if reg_res.status_code == 400: # already registered
        log_res = client.post("/api/auth/login", json={"email": email, "password": pwd})
        token = log_res.json()["access_token"]
    else:
        token = reg_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "cadence_spm": 178.0,
        "step_count": 45,
        "left_right_symmetry_pct": 95.0,
        "trunk_lean_deg": 7.5,
        "duration_sec": 30.0,
        "camera_view": "Side view",
        "camera_suitability": "Good",
        "tracking_quality_pct": 92.0,
        "form_classification": "High-Cadence Live Stride",
        "overall_confidence": "High"
    }

    save_res = client.post("/api/analyses/live", json=payload, headers=headers)
    assert save_res.status_code == 201
    saved_data = save_res.json()
    analysis_id = saved_data["analysis_id"]

    # Verify retrieved by owner
    get_res = client.get(f"/api/analyses/{analysis_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["cadence_spm"] == 178.0

    # Clean up
    del_res = client.delete(f"/api/analyses/{analysis_id}", headers=headers)
    assert del_res.status_code == 200
