"""
Tests for Feature 2: "What Changed?" session-over-session comparison.

Coverage:
1. First analysis returns no comparison (is_first_analysis=True).
2. Second analysis compares against first.
3. Third analysis compares against second, not first.
4. Numeric change calculation is correct.
5. Percentage change calculation is correct.
6. Missing metrics handled safely.
7. User A cannot use User B's previous analysis.
8. Previous analysis lookup is authenticated-user scoped.
9. Personal Goal correctly identifies relevant metric keys.
10. Invalid/missing historical data does not produce fabricated values.
11. Demo Mode remains functional.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.auth.security import create_access_token, get_password_hash
from app.db.session import SessionLocal
from app.db.models import User, UserProfile, Analysis
from app.comparison.comparison_engine import comparison_engine

client = TestClient(app)


# ─── Fixture helpers ─────────────────────────────────────────────────────────

def _make_user(db: Session, prefix: str) -> tuple:
    uid = f"cmp-{prefix}-{uuid.uuid4().hex[:8]}"
    email = f"{prefix}_{uuid.uuid4().hex[:6]}@cmp-test.example.com"
    user = User(id=uid, email=email, password_hash=get_password_hash("Password!1"))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id})
    return user, token


def _make_analysis(db: Session, user_id: str, offset_seconds: int = 0,
                   cadence: float = 172.0, symmetry: float = 91.0, trunk: float = 8.0) -> Analysis:
    """Creates a minimal completed Analysis record directly in the DB."""
    aid = uuid.uuid4().hex
    ts = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    a = Analysis(
        id=aid,
        user_id=user_id,
        video_id=f"vid-{aid[:8]}",
        status="completed",
        cadence_spm=cadence,
        left_right_symmetry_pct=symmetry,
        trunk_lean_deg=trunk,
        raw_payload_json={
            "analysis_id": aid,
            "user_id": user_id,
            "status": "completed",
            "cadence_spm": cadence,
            "left_right_symmetry_pct": symmetry,
            "trunk_lean_deg": trunk,
            "metrics": [
                {"key": "cadence", "name": "Cadence", "value": str(cadence), "unit": "SPM"},
                {"key": "symmetry", "name": "Symmetry", "value": str(symmetry), "unit": "%"},
                {"key": "trunk_lean", "name": "Trunk Lean", "value": str(trunk), "unit": "°"}
            ]
        }
    )
    a.created_at = ts
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


# ─── Test Cases ───────────────────────────────────────────────────────────────

def test_first_analysis_returns_no_comparison():
    """First analysis must return is_first_analysis=True with no metric comparisons."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "cmp1")
        a1 = _make_analysis(db, user.id, offset_seconds=0)
    finally:
        db.close()

    resp = client.get(
        f"/api/analyses/{a1.id}/comparison",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_first_analysis"] is True
    assert data["has_previous"] is False
    assert data["previous_analysis_id"] is None
    assert data["metrics"] == []
    assert "first" in data["comparison_summary"].lower() or "baseline" in data["comparison_summary"].lower()


def test_second_analysis_compares_against_first():
    """Second analysis must compare against the first, not an absent third."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "cmp2")
        a1 = _make_analysis(db, user.id, offset_seconds=0, cadence=170.0, symmetry=90.0)
        a2 = _make_analysis(db, user.id, offset_seconds=100, cadence=174.0, symmetry=93.0)
        a1_id = a1.id  # capture before session closes
        a2_id = a2.id
    finally:
        db.close()

    resp = client.get(
        f"/api/analyses/{a2_id}/comparison",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_first_analysis"] is False
    assert data["has_previous"] is True
    assert data["previous_analysis_id"] == a1_id


def test_third_analysis_compares_against_second_not_first():
    """Third analysis (a3) must compare against a2, never a1."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "cmp3")
        a1 = _make_analysis(db, user.id, offset_seconds=0, cadence=160.0)
        a2 = _make_analysis(db, user.id, offset_seconds=100, cadence=170.0)
        a3 = _make_analysis(db, user.id, offset_seconds=200, cadence=176.0)
        a1_id = a1.id
        a2_id = a2.id
        a3_id = a3.id
    finally:
        db.close()

    resp = client.get(
        f"/api/analyses/{a3_id}/comparison",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["previous_analysis_id"] == a2_id
    assert data["previous_analysis_id"] != a1_id


def test_numeric_change_calculation_is_correct():
    """Verifies absolute_change and percentage_change are accurately computed for cadence."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "cmp4")
        _make_analysis(db, user.id, offset_seconds=0, cadence=172.0)
        a2 = _make_analysis(db, user.id, offset_seconds=100, cadence=176.0)
    finally:
        db.close()

    resp = client.get(
        f"/api/analyses/{a2.id}/comparison",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    cadence_metric = next((m for m in data["metrics"] if m["key"] == "cadence"), None)
    assert cadence_metric is not None
    assert cadence_metric["previous_value"] == 172
    assert cadence_metric["current_value"] == 176
    assert cadence_metric["absolute_change"] == pytest.approx(4.0, abs=0.1)
    # Expected pct: (4/172)*100 = 2.33%
    assert cadence_metric["percentage_change"] == pytest.approx(2.33, abs=0.1)


def test_symmetry_change_uses_percentage_points_not_percent():
    """Symmetry delta must be expressed in percentage points, not relative % change."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "cmp5")
        _make_analysis(db, user.id, offset_seconds=0, symmetry=92.0)
        a2 = _make_analysis(db, user.id, offset_seconds=100, symmetry=95.0)
    finally:
        db.close()

    resp = client.get(
        f"/api/analyses/{a2.id}/comparison",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    sym_metric = next((m for m in data["metrics"] if m["key"] == "symmetry"), None)
    assert sym_metric is not None
    assert sym_metric["unit"] == "percentage points"
    assert sym_metric["absolute_change"] == pytest.approx(3.0, abs=0.1)
    assert sym_metric["percentage_change"] is None  # never % change on symmetry


def test_missing_metrics_handled_safely():
    """If a metric is absent in either session, the comparison row must not fabricate values."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "cmp6")
        # a1 has NO trunk_lean stored
        a1 = Analysis(
            id=uuid.uuid4().hex,
            user_id=user.id,
            video_id="vid-no-trunk",
            status="completed",
            cadence_spm=170.0,
            raw_payload_json={
                "analysis_id": "x",
                "status": "completed",
                "metrics": [{"key": "cadence", "value": "170", "unit": "SPM"}]
            }
        )
        a1.created_at = datetime.now(timezone.utc)
        db.add(a1)
        db.commit()

        a2 = _make_analysis(db, user.id, offset_seconds=100, cadence=174.0, trunk=7.5)
    finally:
        db.close()

    resp = client.get(
        f"/api/analyses/{a2.id}/comparison",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    # Trunk lean should NOT appear since it was absent in a1
    trunk_metric = next((m for m in data["metrics"] if m["key"] == "trunk_lean"), None)
    assert trunk_metric is None


def test_user_isolation_prevents_cross_user_comparison():
    """User A viewing their analysis must NOT compare against User B's previous analysis."""
    db = SessionLocal()
    try:
        user_a, token_a = _make_user(db, "cmpA")
        user_b, _token_b = _make_user(db, "cmpB")

        # User B has many previous sessions
        for i in range(3):
            _make_analysis(db, user_b.id, offset_seconds=i * 100)

        # User A has only one analysis (their first)
        a1_a = _make_analysis(db, user_a.id, offset_seconds=0, cadence=170.0)
    finally:
        db.close()

    resp = client.get(
        f"/api/analyses/{a1_a.id}/comparison",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    data = resp.json()
    # User A's first analysis: must be first analysis state, not compared to B's sessions
    assert data["is_first_analysis"] is True
    assert data["has_previous"] is False


def test_previous_analysis_ownership_verified():
    """User B cannot use /comparison on User A's analysis ID and get User B's data."""
    db = SessionLocal()
    try:
        user_a, token_a = _make_user(db, "cmpOwnA")
        user_b, token_b = _make_user(db, "cmpOwnB")

        a1_a = _make_analysis(db, user_a.id, offset_seconds=0)
        a2_a = _make_analysis(db, user_a.id, offset_seconds=100)
    finally:
        db.close()

    # User B requests comparison on User A's analysis — must get 404
    resp = client.get(
        f"/api/analyses/{a2_a.id}/comparison",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert resp.status_code in [404, 422]


def test_personal_goal_marks_relevant_metrics():
    """Goal IMPROVE_CADENCE should mark cadence as goal_relevant=True."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "cmpGoal")
        # Set IMPROVE_CADENCE goal directly on profile
        profile = UserProfile(
            user_id=user.id,
            goal_type="IMPROVE_CADENCE",
            goal_status="ACTIVE",
            goal_created_at=datetime.now(timezone.utc),
            goal_updated_at=datetime.now(timezone.utc),
        )
        db.add(profile)
        db.commit()

        _make_analysis(db, user.id, offset_seconds=0, cadence=170.0, symmetry=90.0)
        a2 = _make_analysis(db, user.id, offset_seconds=100, cadence=176.0, symmetry=93.0)
    finally:
        db.close()

    resp = client.get(
        f"/api/analyses/{a2.id}/comparison",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    assert data["user_goal"] is not None
    assert data["user_goal"]["type"] == "IMPROVE_CADENCE"

    cadence_metric = next((m for m in data["metrics"] if m["key"] == "cadence"), None)
    assert cadence_metric is not None
    assert cadence_metric["goal_relevant"] is True

    symmetry_metric = next((m for m in data["metrics"] if m["key"] == "symmetry"), None)
    if symmetry_metric:
        # symmetry is NOT in IMPROVE_CADENCE mapping
        assert symmetry_metric["goal_relevant"] is False


def test_demo_mode_returns_safely():
    """Demo analysis /comparison must not crash — expected first-analysis or empty state."""
    resp = client.get("/api/analyses/demo-runner-session-001/comparison")
    # Should return 200 with empty or first-session state
    assert resp.status_code in [200, 404]
    if resp.status_code == 200:
        data = resp.json()
        assert "is_first_analysis" in data or "has_previous" in data
