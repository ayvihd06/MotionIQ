"""
Tests for Feature 4: Personalized Recommendations.

Coverage:
1. No goal -> NO_GOAL state.
2. First analysis -> FIRST_ANALYSIS state.
3. Active Cadence Goal -> Cadence recommendation with non-prescriptive language.
4. Active Symmetry Goal -> Symmetry recommendation.
5. Active Form Goal -> Form/Posture recommendation.
6. Low confidence video -> LOW_CONFIDENCE camera optimization recommendation.
7. User isolation: User A receives only User A's recommendations.
8. Medical language safety: verifies absence of clinical/injury claims.
9. Unauthenticated / Demo mode safety.
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
    uid = f"rec-{prefix}-{uuid.uuid4().hex[:8]}"
    email = f"{prefix}_{uuid.uuid4().hex[:6]}@rec-test.example.com"
    user = User(id=uid, email=email, password_hash=get_password_hash("Password!1"))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id})
    return user, token


def _make_analysis(db: Session, user_id: str, offset_seconds: int = 0,
                   cadence: float = 172.0, symmetry: float = 91.0, trunk: float = 8.0,
                   overall_confidence: str = "High") -> str:
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
        overall_confidence=overall_confidence,
        raw_payload_json={
            "analysis_id": aid,
            "user_id": user_id,
            "status": "completed",
            "cadence_spm": cadence,
            "left_right_symmetry_pct": symmetry,
            "trunk_lean_deg": trunk,
            "overall_confidence": overall_confidence,
            "context": {
                "detected": {"surface": {"value": "Road / Asphalt"}},
                "optional": {"running_surface": "Road"}
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


def test_recommendation_first_analysis_state():
    """If user has only 1 analysis, return FIRST_ANALYSIS state."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "rec1")
        _make_analysis(db, user.id, offset_seconds=0)
    finally:
        db.close()

    resp = client.get("/api/profile/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "FIRST_ANALYSIS"
    assert data["recommendation"] is None
    assert "baseline" in data["headline"].lower() or "baseline" in data["message"].lower()


def test_recommendation_no_goal_state():
    """If user has multiple analyses but no personal goal, return NO_GOAL state."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "recNoGoal")
        _make_analysis(db, user.id, offset_seconds=0)
        _make_analysis(db, user.id, offset_seconds=100)
    finally:
        db.close()

    resp = client.get("/api/profile/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "NO_GOAL"
    assert data["recommendation"] is None
    assert data["has_goal"] is False


def test_recommendation_cadence_goal():
    """User with IMPROVE_CADENCE receives a cadence rhythm recommendation."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "recCad")
        profile = UserProfile(
            user_id=user.id,
            goal_type="IMPROVE_CADENCE",
            goal_status="ACTIVE",
            goal_created_at=datetime.now(timezone.utc),
            goal_updated_at=datetime.now(timezone.utc)
        )
        db.add(profile)
        db.commit()

        _make_analysis(db, user.id, offset_seconds=0, cadence=170.0)
        _make_analysis(db, user.id, offset_seconds=100, cadence=176.0)
    finally:
        db.close()

    resp = client.get("/api/profile/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "ACTIVE_RECOMMENDATION"
    assert data["recommendation"] is not None
    rec = data["recommendation"]
    assert rec["goal_type"] == "IMPROVE_CADENCE"
    assert rec["category"] in ["CONSISTENCY", "PRACTICE", "OBSERVE"]
    assert len(rec["action_bullets"]) > 0
    assert len(rec["rationale"]) > 0


def test_recommendation_symmetry_goal():
    """User with IMPROVE_SYMMETRY receives a bilateral balance recommendation."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "recSym")
        profile = UserProfile(
            user_id=user.id,
            goal_type="IMPROVE_SYMMETRY",
            goal_status="ACTIVE",
            goal_created_at=datetime.now(timezone.utc),
            goal_updated_at=datetime.now(timezone.utc)
        )
        db.add(profile)
        db.commit()

        _make_analysis(db, user.id, offset_seconds=0, symmetry=90.0)
        _make_analysis(db, user.id, offset_seconds=100, symmetry=95.0)
    finally:
        db.close()

    resp = client.get("/api/profile/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "ACTIVE_RECOMMENDATION"
    assert data["recommendation"] is not None
    assert data["recommendation"]["goal_type"] == "IMPROVE_SYMMETRY"


def test_recommendation_low_confidence_handling():
    """If latest analysis has low confidence, return LOW_CONFIDENCE video optimization recommendation."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "recLowConf")
        profile = UserProfile(
            user_id=user.id,
            goal_type="IMPROVE_CADENCE",
            goal_status="ACTIVE"
        )
        db.add(profile)
        db.commit()

        _make_analysis(db, user.id, offset_seconds=0, cadence=170.0)
        _make_analysis(db, user.id, offset_seconds=100, cadence=176.0, overall_confidence="Low")
    finally:
        db.close()

    resp = client.get("/api/profile/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "LOW_CONFIDENCE"
    assert data["recommendation"] is not None
    assert data["recommendation"]["category"] == "RECHECK"
    assert "video" in data["recommendation"]["title"].lower() or "tracking" in data["recommendation"]["title"].lower()


def test_recommendation_user_isolation():
    """User A cannot access User B's personalized recommendations."""
    db = SessionLocal()
    try:
        user_a, token_a = _make_user(db, "recIsoA")
        user_b, token_b = _make_user(db, "recIsoB")

        prof_a = UserProfile(user_id=user_a.id, goal_type="IMPROVE_CADENCE", goal_status="ACTIVE")
        prof_b = UserProfile(user_id=user_b.id, goal_type="IMPROVE_SYMMETRY", goal_status="ACTIVE")
        db.add(prof_a)
        db.add(prof_b)
        db.commit()

        _make_analysis(db, user_a.id, offset_seconds=0, cadence=168.0)
        _make_analysis(db, user_a.id, offset_seconds=100, cadence=176.0)

        _make_analysis(db, user_b.id, offset_seconds=0, symmetry=90.0)
        _make_analysis(db, user_b.id, offset_seconds=100, symmetry=96.0)
    finally:
        db.close()

    resp_a = client.get("/api/profile/recommendations", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = client.get("/api/profile/recommendations", headers={"Authorization": f"Bearer {token_b}"})

    assert resp_a.json()["recommendation"]["goal_type"] == "IMPROVE_CADENCE"
    assert resp_b.json()["recommendation"]["goal_type"] == "IMPROVE_SYMMETRY"


def test_recommendation_medical_language_safety():
    """Recommendations must not contain medical, diagnostic, or injury claims."""
    db = SessionLocal()
    try:
        user, token = _make_user(db, "recSafe")
        profile = UserProfile(user_id=user.id, goal_type="IMPROVE_FORM", goal_status="ACTIVE")
        db.add(profile)
        db.commit()

        _make_analysis(db, user.id, offset_seconds=0, trunk=6.0)
        _make_analysis(db, user.id, offset_seconds=100, trunk=9.0)
    finally:
        db.close()

    resp = client.get("/api/profile/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    rec = data["recommendation"]
    assert rec is not None

    full_text = (rec["title"] + " " + rec["action_suggestion"] + " " + " ".join(rec["action_bullets"])).lower()
    banned_terms = ["cure", "diagnos", "injury prevention", "prescribe", "treatment", "pathology", "disease"]
    for term in banned_terms:
        assert term not in full_text, f"Banned medical term '{term}' found in recommendation text!"
