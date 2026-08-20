"""
Phase 7 Backend Tests -- Personal Runner Profile
=================================================
Tests profile persistence, optional_profile_preferences JSON storage,
user isolation for profile data, and validation of field boundaries.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# -- Helpers -------------------------------------------------------------------

def _register_and_login(email: str, password: str = "SecurePass123!") -> str:
    reg = client.post("/api/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201, f"Registration failed: {reg.text}"
    return reg.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _unique_email() -> str:
    return f"phase7_{uuid.uuid4().hex[:8]}@motioniq.ai"


# -- Test 1: Profile retrieval returns expected defaults -----------------------

def test_profile_get_returns_defaults():
    email = _unique_email()
    token = _register_and_login(email)
    me = client.get("/api/auth/me", headers=_auth_headers(token))
    assert me.status_code == 200
    user_data = me.json()
    assert "profile" in user_data
    profile = user_data["profile"]
    assert profile is not None
    assert "id" in profile
    assert "video_retention_preference" in profile
    prefs = profile.get("optional_profile_preferences")
    assert prefs is None or isinstance(prefs, dict)
    client.delete("/api/auth/account", headers=_auth_headers(token))


# -- Test 2: Standard profile fields persist -----------------------------------

def test_profile_standard_fields_persist():
    email = _unique_email()
    token = _register_and_login(email)
    headers = _auth_headers(token)
    update_payload = {
        "display_name": "Phase7 Runner",
        "age_category": "30-39",
        "height_cm": 172.5,
        "weight_kg": 65.0,
        "running_experience": "Advanced",
        "weekly_running_volume_km": 50.0,
        "typical_easy_pace": "5:10 /km",
        "video_retention_preference": True,
    }
    put_res = client.put("/api/auth/profile", headers=headers, json=update_payload)
    assert put_res.status_code == 200, f"Profile update failed: {put_res.text}"
    data = put_res.json()
    assert data["display_name"] == "Phase7 Runner"
    assert data["age_category"] == "30-39"
    assert data["height_cm"] == 172.5
    assert data["weight_kg"] == 65.0
    assert data["running_experience"] == "Advanced"
    assert data["weekly_running_volume_km"] == 50.0
    assert data["typical_easy_pace"] == "5:10 /km"
    assert data["video_retention_preference"] is True
    me = client.get("/api/auth/me", headers=headers)
    profile_from_me = me.json()["profile"]
    assert profile_from_me["display_name"] == "Phase7 Runner"
    assert profile_from_me["running_experience"] == "Advanced"
    client.delete("/api/auth/account", headers=headers)


# -- Test 3: optional_profile_preferences JSON column stores new fields --------

def test_optional_profile_preferences_persist():
    email = _unique_email()
    token = _register_and_login(email)
    headers = _auth_headers(token)
    new_prefs = {
        "primary_running_goal": "Improve bilateral symmetry",
        "sessions_per_week": 4,
        "preferred_surface": "Road",
        "preferred_training": "Intervals",
        "custom_key": "phase7_test"
    }
    put_res = client.put("/api/auth/profile", headers=headers, json={
        "optional_profile_preferences": new_prefs
    })
    assert put_res.status_code == 200, f"Failed: {put_res.text}"
    returned_prefs = put_res.json().get("optional_profile_preferences", {})
    assert returned_prefs.get("primary_running_goal") == "Improve bilateral symmetry"
    assert returned_prefs.get("sessions_per_week") == 4
    assert returned_prefs.get("preferred_surface") == "Road"
    assert returned_prefs.get("preferred_training") == "Intervals"
    assert returned_prefs.get("custom_key") == "phase7_test"
    me = client.get("/api/auth/me", headers=headers)
    profile_prefs_from_me = me.json()["profile"].get("optional_profile_preferences", {})
    assert profile_prefs_from_me.get("primary_running_goal") == "Improve bilateral symmetry"
    assert profile_prefs_from_me.get("preferred_surface") == "Road"
    client.delete("/api/auth/account", headers=headers)


# -- Test 4: Partial updates do not wipe unrelated fields ----------------------

def test_partial_profile_update_preserves_display_name():
    email = _unique_email()
    token = _register_and_login(email)
    headers = _auth_headers(token)
    client.put("/api/auth/profile", headers=headers, json={
        "display_name": "Alice",
        "running_experience": "Intermediate",
    })
    partial_res = client.put("/api/auth/profile", headers=headers, json={
        "display_name": "Alice Updated"
    })
    assert partial_res.status_code == 200
    data = partial_res.json()
    assert data["display_name"] == "Alice Updated"
    client.delete("/api/auth/account", headers=headers)


# -- Test 5: User isolation -- profiles are not cross-accessible ---------------

def test_profile_user_isolation():
    email_a = _unique_email()
    email_b = _unique_email()
    token_a = _register_and_login(email_a)
    token_b = _register_and_login(email_b)
    headers_a = _auth_headers(token_a)
    headers_b = _auth_headers(token_b)
    client.put("/api/auth/profile", headers=headers_a, json={
        "display_name": "UserA_Profile",
        "optional_profile_preferences": {"primary_running_goal": "UserA_goal"}
    })
    me_b = client.get("/api/auth/me", headers=headers_b)
    assert me_b.status_code == 200
    profile_b = me_b.json()["profile"]
    assert profile_b.get("display_name") != "UserA_Profile"
    prefs_b = profile_b.get("optional_profile_preferences") or {}
    assert prefs_b.get("primary_running_goal") != "UserA_goal"
    me_a = client.get("/api/auth/me", headers=headers_a)
    assert me_a.json()["email"] == email_a.lower()
    client.delete("/api/auth/account", headers=headers_a)
    client.delete("/api/auth/account", headers=headers_b)


# -- Test 6: Unauthenticated profile access is rejected ------------------------

def test_profile_update_requires_authentication():
    res = client.put("/api/auth/profile", json={"display_name": "NoAuth"})
    assert res.status_code == 401


# -- Test 7: Profile update after account deletion is rejected -----------------

def test_profile_update_after_account_deletion():
    email = _unique_email()
    token = _register_and_login(email)
    headers = _auth_headers(token)
    del_res = client.delete("/api/auth/account", headers=headers)
    assert del_res.status_code == 200
    late_update = client.put("/api/auth/profile", headers=headers, json={
        "display_name": "Ghost Runner"
    })
    assert late_update.status_code == 401


# -- Test 8: Display name Unicode encoding -------------------------------------

def test_display_name_encoding():
    email = _unique_email()
    token = _register_and_login(email)
    headers = _auth_headers(token)
    unicode_name = "Senor Runner Phase7"
    put_res = client.put("/api/auth/profile", headers=headers, json={
        "display_name": unicode_name
    })
    assert put_res.status_code == 200
    assert put_res.json()["display_name"] == unicode_name
    me = client.get("/api/auth/me", headers=headers)
    assert me.json()["profile"]["display_name"] == unicode_name
    client.delete("/api/auth/account", headers=headers)


# -- Test 9: Video retention defaults to False and toggles correctly -----------

def test_video_retention_defaults_and_toggles():
    email = _unique_email()
    token = _register_and_login(email)
    headers = _auth_headers(token)
    me = client.get("/api/auth/me", headers=headers)
    profile = me.json()["profile"]
    assert profile["video_retention_preference"] is False
    client.put("/api/auth/profile", headers=headers, json={"video_retention_preference": True})
    me2 = client.get("/api/auth/me", headers=headers)
    assert me2.json()["profile"]["video_retention_preference"] is True
    client.put("/api/auth/profile", headers=headers, json={"video_retention_preference": False})
    me3 = client.get("/api/auth/me", headers=headers)
    assert me3.json()["profile"]["video_retention_preference"] is False
    client.delete("/api/auth/account", headers=headers)
