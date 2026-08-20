import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.analysis_repository import analysis_repository

client = TestClient(app)

def test_user_data_isolation_and_ownership():
    # Register User A
    user_a_email = f"runner_a_{id(object())}@motioniq.ai"
    user_a_pass = "PasswordUserA123!"
    res_a = client.post("/api/auth/register", json={"email": user_a_email, "password": user_a_pass, "display_name": "Runner A"})
    token_a = res_a.json()["access_token"]
    user_a_id = res_a.json()["user"]["id"]

    # 2. Register User B
    user_b_email = f"runner_b_{id(object())}@motioniq.ai"
    res_b = client.post("/api/auth/register", json={"email": user_b_email, "password": "Password123!"})
    token_b = res_b.json()["access_token"]
    user_b_id = res_b.json()["user"]["id"]

    # Create Analysis owned by User A
    analysis_id_a = f"analysis-user-a-{id(object())}"
    record_a = {
        "analysis_id": analysis_id_a,
        "user_id": user_a_id,
        "video_id": "video-a",
        "created_at": "2026-08-19T18:00:00",
        "status": "completed",
        "progress_percentage": 100,
        "current_step": "Phase 4 Analysis Complete",
        "annotated_video_url": f"/api/analyses/{analysis_id_a}/video",
        "cadence_spm": 176.0,
        "step_count": 14,
        "left_right_symmetry_pct": 96.0,
        "trunk_lean_deg": 7.0,
        "left_mean_step_time_s": 0.34,
        "right_mean_step_time_s": 0.34,
        "mean_stride_time_s": 0.68,
        "step_time_variability_cv": 3.2,
        "mean_elbow_angle_deg": 88.0,
        "overstride_risk": "Low Risk",
        "foot_strike_pattern": "Midfoot-dominant",
        "relative_vertical_movement_proxy": 0.11,
        "form_classification": "Dynamic Stride",
        "overall_confidence": "High",
        "metrics_breakdown": [
            {"key": "cadence", "name": "Cadence", "value": "176", "unit": "SPM", "confidence": "High", "status": "Optimal", "description": "Step rate"}
        ],
        "context": {
            "video_id": "video-a",
            "detected": {
                "duration_sec": 4.5,
                "fps": 30.0,
                "resolution": "1920x1080",
                "video_format": ".mp4",
                "quality_status": "Optimal",
                "runner_count": {"value": 1, "source": "pose_analysis", "confidence": 0.98},
                "full_body_visible": {"value": True, "source": "pose_analysis", "confidence": 0.95},
                "camera_view": {"value": "Side view", "source": "video_metadata", "confidence": 0.95},
                "camera_stability": {"value": "Stationary / Stable", "source": "computer_vision", "confidence": 0.92},
                "observed_movement": {"value": "Running", "source": "computer_vision", "confidence": 0.96},
                "surface": {"value": "Road / Asphalt", "source": "computer_vision", "confidence": 0.90},
                "running_pace_status": {"value": "Estimated", "source": "computer_vision", "confidence": 0.80},
                "pace_estimation_mode": "Uncalibrated video",
                "historical_baseline_status": "First session"
            },
            "optional": {}
        },
        "video_metadata": {
            "filename": "runner.mp4",
            "file_size_bytes": 1048576,
            "duration_sec": 4.5,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "frame_count": 135,
            "format": ".mp4"
        },
        "suitability": {
            "overall_status": "Ready for analysis",
            "suitability_score": 90,
            "checks": [],
            "warnings": [],
            "recommendations": []
        },
        "context_insights": [],
        "recommendations": [],
        "limitations": []
    }
    analysis_repository.save_analysis(analysis_id_a, record_a, user_id=user_a_id)

    # 1. User A can retrieve their own analysis
    get_a = client.get(f"/api/analyses/{analysis_id_a}", headers={"Authorization": f"Bearer {token_a}"})
    assert get_a.status_code == 200
    assert get_a.json()["analysis_id"] == analysis_id_a

    # 2. User B CANNOT retrieve User A's analysis (Data Isolation!)
    get_b = client.get(f"/api/analyses/{analysis_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 404

    # 3. User B's list_analyses does NOT contain User A's analysis
    list_b = client.get("/api/analyses", headers={"Authorization": f"Bearer {token_b}"})
    assert list_b.status_code == 200
    assert not any(item["analysis_id"] == analysis_id_a for item in list_b.json())

    # 4. User B CANNOT delete User A's analysis
    del_b = client.delete(f"/api/analyses/{analysis_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code == 404

    # 5. User A can delete their own analysis
    del_a = client.delete(f"/api/analyses/{analysis_id_a}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_a.status_code == 200

    # Cleanup accounts
    client.delete("/api/auth/account", headers={"Authorization": f"Bearer {token_a}"})
    client.delete("/api/auth/account", headers={"Authorization": f"Bearer {token_b}"})

def test_login_as_different_users_full_flow():
    """Validates the 10-step multi-user login, history isolation, and Personal Form Evolution isolation workflow."""
    
    # 1. Login/Register as User A
    email_a = f"test_a_{id(object())}@motioniq.ai"
    pwd_a = "SecretPassA123!"
    reg_a = client.post("/api/auth/register", json={"email": email_a, "password": pwd_a, "display_name": "Runner A"})
    assert reg_a.status_code == 201
    user_a_id = reg_a.json()["user"]["id"]
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Create 2 analysis records for User A
    a1_id = f"analysis-a1-{id(object())}"
    a2_id = f"analysis-a2-{id(object())}"
    
    def make_analysis(analysis_id, user_id, cadence, symmetry, lean):
        return {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "video_id": f"vid-{analysis_id}",
            "created_at": "2026-08-19T10:00:00",
            "status": "completed",
            "progress_percentage": 100,
            "current_step": "Completed",
            "cadence_spm": cadence,
            "step_count": 14,
            "left_right_symmetry_pct": symmetry,
            "trunk_lean_deg": lean,
            "foot_strike_pattern": "Midfoot-dominant",
            "overstride_risk": "Low Risk",
            "relative_vertical_movement_proxy": 0.11,
            "form_classification": "Dynamic Midfoot Stride",
            "overall_confidence": "High",
            "metrics_breakdown": [
                {"key": "cadence", "name": "Cadence", "value": str(cadence), "unit": "SPM", "confidence": "High", "status": "Optimal"}
            ],
            "context": {
                "video_id": f"vid-{analysis_id}",
                "detected": {
                    "duration_sec": 4.5, "fps": 30.0, "resolution": "1920x1080", "video_format": ".mp4", "quality_status": "Optimal",
                    "runner_count": {"value": 1, "source": "pose_analysis", "confidence": 0.98},
                    "full_body_visible": {"value": True, "source": "pose_analysis", "confidence": 0.95},
                    "camera_view": {"value": "Side view", "source": "video_metadata", "confidence": 0.95},
                    "camera_stability": {"value": "Stationary", "source": "cv", "confidence": 0.92},
                    "observed_movement": {"value": "Running", "source": "cv", "confidence": 0.96},
                    "surface": {"value": "Road", "source": "cv", "confidence": 0.90},
                    "running_pace_status": {"value": "Estimated", "source": "cv", "confidence": 0.80},
                    "pace_estimation_mode": "Uncalibrated", "historical_baseline_status": "Session"
                },
                "optional": {}
            },
            "video_metadata": {"filename": "run.mp4", "file_size_bytes": 1024, "duration_sec": 4.5, "fps": 30.0, "width": 1920, "height": 1080, "frame_count": 135, "format": ".mp4"},
            "suitability": {"overall_status": "Ready for analysis", "suitability_score": 90, "checks": [], "warnings": [], "recommendations": []},
            "context_insights": [], "recommendations": [], "limitations": []
        }

    analysis_repository.save_analysis(a1_id, make_analysis(a1_id, user_a_id, 174.0, 94.0, 7.0), user_id=user_a_id)
    analysis_repository.save_analysis(a2_id, make_analysis(a2_id, user_a_id, 178.0, 96.0, 7.2), user_id=user_a_id)

    # 3. Verify User A history contains only A1 and A2
    hist_a = client.get("/api/analyses", headers=headers_a)
    assert hist_a.status_code == 200
    a_ids = [item["analysis_id"] for item in hist_a.json()]
    assert a1_id in a_ids and a2_id in a_ids
    assert len(a_ids) == 2

    # 4. Verify User A Personal Form Evolution uses only User A data (2 sessions -> Early baseline)
    evo_a = client.get("/api/evolution", headers=headers_a)
    assert evo_a.status_code == 200
    evo_a_data = evo_a.json()
    assert evo_a_data["total_analyses"] == 2
    assert evo_a_data["baseline_status"] == "Early baseline"
    assert evo_a_data["personal_baseline"]["cadence_spm"] == 176.0 # (174 + 178)/2

    # 5. Register and Login as User B
    email_b = f"test_b_{id(object())}@motioniq.ai"
    pwd_b = "SecretPassB456!"
    reg_b = client.post("/api/auth/register", json={"email": email_b, "password": pwd_b, "display_name": "Runner B"})
    assert reg_b.status_code == 201
    user_b_id = reg_b.json()["user"]["id"]
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 6. Verify User A data is NOT visible to User B in history
    hist_b_initial = client.get("/api/analyses", headers=headers_b)
    assert hist_b_initial.status_code == 200
    assert len(hist_b_initial.json()) == 0

    # 7. Create 1 analysis for User B
    b1_id = f"analysis-b1-{id(object())}"
    analysis_repository.save_analysis(b1_id, make_analysis(b1_id, user_b_id, 160.0, 92.0, 5.0), user_id=user_b_id)

    # 8. Verify only User B history appears for User B
    hist_b = client.get("/api/analyses", headers=headers_b)
    assert hist_b.status_code == 200
    b_ids = [item["analysis_id"] for item in hist_b.json()]
    assert b_ids == [b1_id]
    assert a1_id not in b_ids and a2_id not in b_ids

    # 9. Verify User B Personal Form Evolution uses only User B data (1 session -> Baseline unavailable)
    evo_b = client.get("/api/evolution", headers=headers_b)
    assert evo_b.status_code == 200
    evo_b_data = evo_b.json()
    assert evo_b_data["total_analyses"] == 1
    assert evo_b_data["baseline_status"] == "Baseline unavailable"
    assert evo_b_data["personal_baseline"] is None # Needs 2+ sessions

    # 10. Attempt to access User A's analysis using User B's token -> Verify 404
    unauth_get = client.get(f"/api/analyses/{a1_id}", headers=headers_b)
    assert unauth_get.status_code == 404

    unauth_del = client.delete(f"/api/analyses/{a1_id}", headers=headers_b)
    assert unauth_del.status_code == 404

    # Cleanup
    client.delete("/api/auth/account", headers=headers_a)
    client.delete("/api/auth/account", headers=headers_b)

