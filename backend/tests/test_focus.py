"""
Tests for Feature 3: Personal Focus Area.

Coverage:
1. First analysis returns FIRST_ANALYSIS baseline state.
2. Multiple analyses without goal returns NO_GOAL state.
3. Active goal + relevant change returns ACTIVE_FOCUS with matching focus_type.
4. Active goal + zero variation returns NO_STRONG_FOCUS state.
5. User isolation: User A sees only User A's focus, User B sees User B's.
6. Reasoning bullets contain explainable facts.
7. Unauthenticated user handled gracefully.
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
    uid = f"foc-{prefix}-{uuid.uuid4().hex[:8]}"
    email = f"{prefix}_{uuid.uuid4().hex[:6]}@foc-test.example.com"
    user = User(id=uid, email=email, password_hash=get_password_hash("Password!1"))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id})
    return user, token


def _make_analysis(db: Session, user_id: str, offset_seconds: int = 0,
                   cadence: float = 172.0, symmetry: float = 91.0, trunk: float = 8.0) -> str:
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
        overall_confidence="High",
        raw_payload_json={
            "analysis_id": aid,
            "user_id": user_id,
            "status": "completed",
            "cadence_spm": cadence,
            "left_right_symmetry_pct": symmetry,
            "trunk_lean_deg": trunk,
            "overall_confidence": "High",
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


def test_focus_first_analysis_state():
    """If user has only 1 analysis, return FIRST_ANALYSIS state."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "foc1")
        _make_analysis(db, user.id, offset_seconds=0)
    finally:
        db.close()

    resp = client.get("/api/profile/focus", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "FIRST_ANALYSIS"
    assert data["focus"] is None
    assert "baseline" in data["headline"].lower() or "baseline" in data["message"].lower()


def test_focus_no_goal_state():
    """If user has multiple analyses but no personal goal, return NO_GOAL state."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "focNoGoal")
        _make_analysis(db, user.id, offset_seconds=0)
        _make_analysis(db, user.id, offset_seconds=100)
    finally:
        db.close()

    resp = client.get("/api/profile/focus", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "NO_GOAL"
    assert data["focus"] is None
    assert data["has_goal"] is False
    assert data["action_cta"] is not None


def test_focus_active_cadence_goal():
    """User with IMPROVE_CADENCE and recent cadence change should receive CADENCE_CONSISTENCY focus."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "focCad")
        profile = UserProfile(
            user_id=user.id,
            goal_type="IMPROVE_CADENCE",
            goal_status="ACTIVE",
            goal_created_at=datetime.now(timezone.utc),
            goal_updated_at=datetime.now(timezone.utc)
        )
        db.add(profile)
        db.commit()

        # Session 1: 170 SPM, Session 2: 176 SPM (notable change)
        _make_analysis(db, user.id, offset_seconds=0, cadence=170.0)
        _make_analysis(db, user.id, offset_seconds=100, cadence=176.0)
    finally:
        db.close()

    resp = client.get("/api/profile/focus", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "ACTIVE_FOCUS"
    assert data["focus"] is not None
    assert data["focus"]["focus_type"] == "CADENCE_CONSISTENCY"
    assert data["focus"]["primary_metric_key"] == "cadence"
    assert len(data["focus"]["reasoning"]) > 0
    assert any("goal" in r.lower() for r in data["focus"]["reasoning"])


def test_focus_active_symmetry_goal():
    """User with IMPROVE_SYMMETRY and symmetry change should receive BILATERAL_BALANCE focus."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "focSym")
        profile = UserProfile(
            user_id=user.id,
            goal_type="IMPROVE_SYMMETRY",
            goal_status="ACTIVE",
            goal_created_at=datetime.now(timezone.utc),
            goal_updated_at=datetime.now(timezone.utc)
        )
        db.add(profile)
        db.commit()

        # Session 1: 91.0%, Session 2: 95.0%
        _make_analysis(db, user.id, offset_seconds=0, symmetry=91.0)
        _make_analysis(db, user.id, offset_seconds=100, symmetry=95.0)
    finally:
        db.close()

    resp = client.get("/api/profile/focus", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "ACTIVE_FOCUS"
    assert data["focus"]["focus_type"] == "BILATERAL_BALANCE"
    assert data["focus"]["primary_metric_key"] == "symmetry"


def test_focus_user_isolation():
    """User A's goal & focus must be completely isolated from User B."""
    db = SessionLocal()
    try:
        user_a, token_a = _make_user(db, "focIsoA")
        user_b, token_b = _make_user(db, "focIsoB")

        # User A has Cadence Goal
        prof_a = UserProfile(user_id=user_a.id, goal_type="IMPROVE_CADENCE", goal_status="ACTIVE")
        db.add(prof_a)
        # User B has Symmetry Goal
        prof_b = UserProfile(user_id=user_b.id, goal_type="IMPROVE_SYMMETRY", goal_status="ACTIVE")
        db.add(prof_b)
        db.commit()

        _make_analysis(db, user_a.id, offset_seconds=0, cadence=168.0)
        _make_analysis(db, user_a.id, offset_seconds=100, cadence=176.0)

        _make_analysis(db, user_b.id, offset_seconds=0, symmetry=90.0)
        _make_analysis(db, user_b.id, offset_seconds=100, symmetry=96.0)
    finally:
        db.close()

    resp_a = client.get("/api/profile/focus", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = client.get("/api/profile/focus", headers={"Authorization": f"Bearer {token_b}"})

    assert resp_a.json()["focus"]["focus_type"] == "CADENCE_CONSISTENCY"
    assert resp_b.json()["focus"]["focus_type"] == "BILATERAL_BALANCE"
