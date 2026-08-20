import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.auth.security import create_access_token, get_password_hash
from app.db.session import SessionLocal
from app.db.models import User, Analysis
from app.repositories.analysis_repository import analysis_repository
from app.milestones.milestone_service import milestone_service

client = TestClient(app)

@pytest.fixture
def clean_db():
    db = SessionLocal()
    try:
        # Create two distinct test users for isolation testing
        u1_id = f"test-runner-1-{uuid.uuid4().hex[:8]}"
        u2_id = f"test-runner-2-{uuid.uuid4().hex[:8]}"
        
        user1 = User(
            id=u1_id,
            email=f"runner1_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=get_password_hash("Password123!")
        )
        user2 = User(
            id=u2_id,
            email=f"runner2_{uuid.uuid4().hex[:6]}@example.com",
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


def test_milestone_calculation_logic():
    """Unit test for MilestoneService pure calculation engine."""
    t0 = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    t1 = datetime(2026, 8, 5, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    t2 = datetime(2026, 8, 10, 10, 0, 0, tzinfo=timezone.utc).isoformat()

    analyses = [
        {
            "id": "run-1",
            "created_at": t0,
            "status": "completed",
            "cadence_spm": 168.0,
            "left_right_symmetry_pct": 91.0,
            "form_consistency_score": 82.0
        },
        {
            "id": "run-2",
            "created_at": t1,
            "status": "completed",
            "cadence_spm": 174.0,
            "left_right_symmetry_pct": 96.5,
            "form_consistency_score": 88.0
        },
        {
            "id": "run-3",
            "created_at": t2,
            "status": "completed",
            "cadence_spm": 172.0,
            "left_right_symmetry_pct": 94.0,
            "form_consistency_score": 85.0
        }
    ]

    report = milestone_service.calculate_milestones(analyses)
    assert report["total_analyses"] == 3
    assert report["has_milestones"] is True

    milestones_by_type = {m["type"]: m for m in report["milestones"]}

    # Best Symmetry
    best_symm = milestones_by_type["best_symmetry"]
    assert best_symm["value"] == 96.5
    assert best_symm["analysis_id"] == "run-2"
    assert best_symm["previous_value"] == 91.0
    assert best_symm["improvement_delta"] == 5.5
    assert best_symm["improvement_unit"] == "percentage points"

    # Highest Cadence
    best_cad = milestones_by_type["highest_cadence"]
    assert best_cad["value"] == 174.0
    assert best_cad["analysis_id"] == "run-2"
    assert best_cad["previous_value"] == 168.0
    assert best_cad["improvement_delta"] == 6.0
    assert best_cad["unit"] == "SPM"

    # Most Consistent Session
    best_cons = milestones_by_type["best_consistency"]
    assert best_cons["value"] == 88.0
    assert best_cons["analysis_id"] == "run-2"

    # Biggest Improvement
    biggest_imp = milestones_by_type["biggest_improvement"]
    assert biggest_imp["value"] == 5.5
    assert biggest_imp["unit"] == "percentage points"
    assert biggest_imp["analysis_id"] == "run-2"
    assert biggest_imp["comparison_analysis_id"] == "run-1"

    # Analysis Streak
    streak = milestones_by_type["analysis_streak"]
    assert streak["value"] == 3
    assert streak["unit"] == "sessions"


def test_empty_and_single_session_milestones():
    """Verify first-session and empty-state handling."""
    # 0 sessions
    empty_report = milestone_service.calculate_milestones([])
    assert empty_report["total_analyses"] == 0
    assert empty_report["has_milestones"] is False
    assert empty_report["empty_state"]["action_label"] == "Analyze Your First Run"

    # 1 session
    single = [{
        "id": "solo-1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "cadence_spm": 175.0,
        "left_right_symmetry_pct": 95.0,
        "form_consistency_score": 90.0
    }]
    single_report = milestone_service.calculate_milestones(single)
    assert single_report["total_analyses"] == 1
    assert single_report["has_milestones"] is True
    
    m_types = {m["type"]: m for m in single_report["milestones"]}
    assert m_types["best_symmetry"]["value"] == 95.0
    assert m_types["best_symmetry"]["previous_value"] is None
    # Biggest improvement should indicate it unlocks after 2 sessions
    assert m_types["biggest_improvement"]["value"] is None


def test_milestones_api_unauthenticated():
    """Unauthenticated GET /api/milestones should return empty state without 500 error."""
    resp = client.get("/api/milestones")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_analyses"] == 0
    assert data["has_milestones"] is False


def test_user_milestone_isolation(clean_db):
    """User A must see only User A's milestones, and User B sees only User B's."""
    u1_id = clean_db["user1"].id
    u2_id = clean_db["user2"].id
    token1 = clean_db["token1"]
    token2 = clean_db["token2"]

    # Save 2 analyses for User 1 (high symmetry 98%)
    a1 = {
        "analysis_id": f"u1-a1-{uuid.uuid4().hex[:6]}",
        "user_id": u1_id,
        "cadence_spm": 185.0,
        "left_right_symmetry_pct": 98.0,
        "form_consistency_score": 95.0,
        "created_at": "2026-08-01T10:00:00Z"
    }
    analysis_repository.save_analysis(a1["analysis_id"], a1, user_id=u1_id)

    # Save 1 analysis for User 2 (symmetry 88%)
    a2 = {
        "analysis_id": f"u2-a1-{uuid.uuid4().hex[:6]}",
        "user_id": u2_id,
        "cadence_spm": 160.0,
        "left_right_symmetry_pct": 88.0,
        "form_consistency_score": 80.0,
        "created_at": "2026-08-02T10:00:00Z"
    }
    analysis_repository.save_analysis(a2["analysis_id"], a2, user_id=u2_id)

    # Query User 1
    resp1 = client.get("/api/milestones", headers={"Authorization": f"Bearer {token1}"})
    assert resp1.status_code == 200
    m1 = {m["type"]: m for m in resp1.json()["milestones"]}
    assert m1["best_symmetry"]["value"] == 98.0
    assert m1["highest_cadence"]["value"] == 185.0

    # Query User 2
    resp2 = client.get("/api/milestones", headers={"Authorization": f"Bearer {token2}"})
    assert resp2.status_code == 200
    m2 = {m["type"]: m for m in resp2.json()["milestones"]}
    assert m2["best_symmetry"]["value"] == 88.0
    assert m2["highest_cadence"]["value"] == 160.0

    # User 2 cannot celebrate User 1's analysis
    resp_cross = client.get(
        f"/api/milestones/celebration/{a1['analysis_id']}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert resp_cross.status_code == 404
