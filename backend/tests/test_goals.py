import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.auth.security import create_access_token, get_password_hash
from app.db.session import SessionLocal
from app.db.models import User, UserProfile

client = TestClient(app)

@pytest.fixture
def clean_users():
    db = SessionLocal()
    try:
        u1_id = f"test-goal-u1-{uuid.uuid4().hex[:8]}"
        u2_id = f"test-goal-u2-{uuid.uuid4().hex[:8]}"
        
        user1 = User(
            id=u1_id,
            email=f"goal_u1_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=get_password_hash("Password123!")
        )
        user2 = User(
            id=u2_id,
            email=f"goal_u2_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=get_password_hash("Password123!")
        )
        db.add(user1)
        db.add(user2)
        db.commit()

        token1 = create_access_token({"sub": user1.id})
        token2 = create_access_token({"sub": user2.id})

        yield {
            "user1": user1,
            "user2": user2,
            "token1": token1,
            "token2": token2
        }
    finally:
        db.close()


def test_unauthenticated_goal_access():
    """Unauthenticated access must be rejected with 401."""
    resp_get = client.get("/api/profile/goal")
    assert resp_get.status_code == 401

    resp_put = client.put("/api/profile/goal", json={"type": "IMPROVE_CADENCE"})
    assert resp_put.status_code == 401


def test_empty_goal_state(clean_users):
    """A new user has no goal set initially."""
    token = clean_users["token1"]
    resp = client.get("/api/profile/goal", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["goal"] is None
    assert len(data["available_goals"]) == 6


def test_set_and_get_personal_goal(clean_users):
    """Authenticated user can set and retrieve their goal."""
    token = clean_users["token1"]

    payload = {
        "type": "IMPROVE_CADENCE",
        "description": "Increase stride frequency towards 180 SPM."
    }
    resp = client.put("/api/profile/goal", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["goal"] is not None
    assert data["goal"]["type"] == "IMPROVE_CADENCE"
    assert data["goal"]["title"] == "Improve Cadence"
    assert data["goal"]["description"] == "Increase stride frequency towards 180 SPM."
    assert data["goal"]["status"] == "ACTIVE"
    assert data["goal"]["created_at"] is not None

    # Retrieve goal
    resp_get = client.get("/api/profile/goal", headers={"Authorization": f"Bearer {token}"})
    assert resp_get.status_code == 200
    get_data = resp_get.json()
    assert get_data["goal"]["type"] == "IMPROVE_CADENCE"
    assert get_data["goal"]["description"] == "Increase stride frequency towards 180 SPM."


def test_update_and_complete_goal(clean_users):
    """User can update their goal and mark it as COMPLETED."""
    token = clean_users["token1"]

    # 1. Set initial goal
    client.put("/api/profile/goal", json={"type": "IMPROVE_SYMMETRY"}, headers={"Authorization": f"Bearer {token}"})

    # 2. Mark as completed
    resp_comp = client.patch("/api/profile/goal/complete", headers={"Authorization": f"Bearer {token}"})
    assert resp_comp.status_code == 200
    assert resp_comp.json()["goal"]["status"] == "COMPLETED"

    # 3. Update to a new goal
    resp_update = client.put(
        "/api/profile/goal",
        json={"type": "IMPROVE_EFFICIENCY", "description": "Focus on smooth aerobic endurance."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["goal"]["type"] == "IMPROVE_EFFICIENCY"
    assert resp_update.json()["goal"]["status"] == "ACTIVE"


def test_invalid_goal_type(clean_users):
    """Invalid goal types must be rejected."""
    token = clean_users["token1"]
    resp = client.put(
        "/api/profile/goal",
        json={"type": "INVALID_GOAL_TYPE"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 422


def test_goal_user_isolation(clean_users):
    """User A's goal is strictly isolated from User B."""
    token1 = clean_users["token1"]
    token2 = clean_users["token2"]

    # User 1 sets Cadence goal
    client.put(
        "/api/profile/goal",
        json={"type": "IMPROVE_CADENCE", "description": "User 1 focus"},
        headers={"Authorization": f"Bearer {token1}"}
    )

    # User 2 sets Form goal
    client.put(
        "/api/profile/goal",
        json={"type": "IMPROVE_FORM", "description": "User 2 focus"},
        headers={"Authorization": f"Bearer {token2}"}
    )

    # User 1 gets only User 1's goal
    resp1 = client.get("/api/profile/goal", headers={"Authorization": f"Bearer {token1}"})
    assert resp1.json()["goal"]["type"] == "IMPROVE_CADENCE"
    assert resp1.json()["goal"]["description"] == "User 1 focus"

    # User 2 gets only User 2's goal
    resp2 = client.get("/api/profile/goal", headers={"Authorization": f"Bearer {token2}"})
    assert resp2.json()["goal"]["type"] == "IMPROVE_FORM"
    assert resp2.json()["goal"]["description"] == "User 2 focus"
