import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_registration_and_login_flow():
    email = f"runner_{id(object())}@motioniq.ai"
    password = "SecurePassword123!"

    # 1. Register User
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "display_name": "Test Marathoner"
    })
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["user"]["email"] == email.lower()
    assert reg_data["user"]["profile"]["display_name"] == "Test Marathoner"
    assert "access_token" in reg_data
    token = reg_data["access_token"]

    # 2. Duplicate Registration Rejection
    dup_res = client.post("/api/auth/register", json={
        "email": email,
        "password": password
    })
    assert dup_res.status_code == 400

    # 3. Invalid Login Credentials
    bad_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # 4. Successful Login
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    login_token = login_res.json()["access_token"]

    # 5. Authenticated /api/auth/me Request
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email.lower()

    # 6. Update User Profile
    prof_res = client.put(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {login_token}"},
        json={
            "age_category": "30-39",
            "height_cm": 178.0,
            "weight_kg": 72.0,
            "running_experience": "Advanced",
            "weekly_running_volume_km": 45.0,
            "typical_easy_pace": "5:15 /km"
        }
    )
    assert prof_res.status_code == 200
    assert prof_res.json()["height_cm"] == 178.0
    assert prof_res.json()["running_experience"] == "Advanced"

    # 7. Logout
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # 8. Delete Account (Purge)
    del_res = client.delete("/api/auth/account", headers={"Authorization": f"Bearer {login_token}"})
    assert del_res.status_code == 200

    # Verify user no longer exists
    recheck = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login_token}"})
    assert recheck.status_code == 401
