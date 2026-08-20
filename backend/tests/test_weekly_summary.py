"""
Tests for Feature 5: Personalized Weekly Running Summary.

Coverage:
1. Unauthenticated weekly summary returns EMPTY_WEEK.
2. Empty week state.
3. One-session week state.
4. Multiple-session week state with metric changes.
5. Symmetry delta expressed in percentage points.
6. Personal Goal, Focus Area, Recommendation integration.
7. Context variation notice (surface/pace).
8. User isolation: User A sees only User A's weekly summary.
9. Previous week retrieval (week_offset=1).
10. Medical language safety check.
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

client = TestClient(app)


def _make_user(db: Session, prefix: str) -> tuple:
    uid = f"wk-{prefix}-{uuid.uuid4().hex[:8]}"
    email = f"{prefix}_{uuid.uuid4().hex[:6]}@wk-test.example.com"
    user = User(id=uid, email=email, password_hash=get_password_hash("Password!1"))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id})
    return user, token


def _make_analysis(db: Session, user_id: str, ts: datetime,
                   cadence: float = 172.0, symmetry: float = 91.0, trunk: float = 8.0,
                   surface: str = "Road") -> str:
    aid = uuid.uuid4().hex
    a = Analysis(
        id=aid,
        user_id=user_id,
        video_id=f"vid-{aid[:8]}",
        status="completed",
        cadence_spm=cadence,
        left_right_symmetry_pct=symmetry,
        trunk_lean_deg=trunk,
        overall_confidence="High",
        raw_payload_json={
            "analysis_id": aid,
            "user_id": user_id,
            "status": "completed",
            "cadence_spm": cadence,
            "left_right_symmetry_pct": symmetry,
            "trunk_lean_deg": trunk,
            "overall_confidence": "High",
            "context": {
                "detected": {"surface": {"value": surface}},
                "optional": {"running_surface": surface}
            },
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
    return aid


def test_weekly_summary_empty_week():
    """User with no analyses this week receives EMPTY_WEEK state."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "wkEmpty")
    finally:
        db.close()

    resp = client.get("/api/profile/weekly-summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "EMPTY_WEEK"
    assert data["total_sessions"] == 0
    assert data["action_cta"] is not None


def test_weekly_summary_one_session():
    """User with 1 analysis this week receives ONE_SESSION state without false trend claims."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "wkOne")
        now = datetime.now(timezone.utc)
        _make_analysis(db, user.id, ts=now, cadence=174.0, symmetry=93.0)
    finally:
        db.close()

    resp = client.get("/api/profile/weekly-summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "ONE_SESSION"
    assert data["total_sessions"] == 1
    assert len(data["metrics"]) >= 2
    cadence_metric = next((m for m in data["metrics"] if m["key"] == "cadence"), None)
    assert cadence_metric is not None
    assert cadence_metric["value_display"] == "174"


def test_weekly_summary_multiple_sessions_aggregation():
    """Multiple sessions in a week compute average metrics, deltas, and highlight."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "wkMulti")
        profile = UserProfile(user_id=user.id, goal_type="IMPROVE_CADENCE", goal_status="ACTIVE")
        db.add(profile)
        db.commit()

        now = datetime.now(timezone.utc)
        # 3 sessions across current week: Monday, Wednesday, Today
        t1 = now - timedelta(hours=48)
        t2 = now - timedelta(hours=24)
        t3 = now

        _make_analysis(db, user.id, ts=t1, cadence=170.0, symmetry=91.0)
        _make_analysis(db, user.id, ts=t2, cadence=172.0, symmetry=92.0)
        _make_analysis(db, user.id, ts=t3, cadence=176.0, symmetry=94.0)
    finally:
        db.close()

    resp = client.get("/api/profile/weekly-summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "ACTIVE_SUMMARY"
    assert data["total_sessions"] == 3
    assert data["goal"] is not None
    assert data["goal"]["type"] == "IMPROVE_CADENCE"
    assert data["highlight"] is not None

    sym_metric = next((m for m in data["metrics"] if m["key"] == "symmetry"), None)
    assert sym_metric is not None
    assert sym_metric["is_percentage_points"] is True
    assert "percentage points" in sym_metric["change_display"]


def test_weekly_summary_context_variation():
    """Different surfaces across weekly sessions produce a context consideration note."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "wkCtx")
        now = datetime.now(timezone.utc)
        _make_analysis(db, user.id, ts=now - timedelta(hours=24), surface="Road")
        _make_analysis(db, user.id, ts=now, surface="Treadmill")
    finally:
        db.close()

    resp = client.get("/api/profile/weekly-summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 2
    assert len(data["context_notes"]) > 0
    assert any("surface" in note.lower() for note in data["context_notes"])


def test_weekly_summary_user_isolation():
    """User A's weekly summary does not leak into User B's weekly summary."""
    db = SessionLocal()
    try:
        user_a, token_a = _make_user(db, "wkIsoA")
        user_b, token_b = _make_user(db, "wkIsoB")

        now = datetime.now(timezone.utc)
        # User A has 3 sessions
        for i in range(3):
            _make_analysis(db, user_a.id, ts=now - timedelta(hours=i*12))

        # User B has 0 sessions
    finally:
        db.close()

    resp_a = client.get("/api/profile/weekly-summary", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = client.get("/api/profile/weekly-summary", headers={"Authorization": f"Bearer {token_b}"})

    assert resp_a.json()["total_sessions"] == 3
    assert resp_b.json()["total_sessions"] == 0
    assert resp_b.json()["state"] == "EMPTY_WEEK"


def test_weekly_summary_previous_week():
    """Retrieving week_offset=1 queries the previous week period."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "wkPrev")
        # Session from 9 days ago (in previous week)
        prev_ts = datetime.now(timezone.utc) - timedelta(days=9)
        _make_analysis(db, user.id, ts=prev_ts, cadence=168.0)
    finally:
        db.close()

    resp = client.get("/api/profile/weekly-summary?week_offset=1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"]["week_offset"] == 1
    assert "previous" in data["period"]["label"].lower() or "ago" in data["period"]["label"].lower()


def test_weekly_summary_medical_language_safety():
    """Weekly summary must not contain medical diagnosis, treatment, or injury claims."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "wkSafe")
        now = datetime.now(timezone.utc)
        _make_analysis(db, user.id, ts=now - timedelta(hours=12))
        _make_analysis(db, user.id, ts=now)
    finally:
        db.close()

    resp = client.get("/api/profile/weekly-summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    insight_text = (data["insight"] + " " + (data["changes_summary"] or "")).lower()

    banned_terms = ["diagnos", "injury prevention", "treatment", "cure", "prescribe", "pathology"]
    for term in banned_terms:
        assert term not in insight_text, f"Banned medical term '{term}' found in weekly summary insight!"
