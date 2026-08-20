import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Boolean, Float, Integer, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class User(Base):
    """User account model for authentication and data isolation."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    profile = relationship("UserProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    """Optional runner profile settings for customized biomechanical context."""
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    age_category = Column(String(50), nullable=True) # e.g. "30-39"
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    running_experience = Column(String(50), nullable=True) # e.g. "Intermediate", "Advanced"
    weekly_running_volume_km = Column(Float, nullable=True)
    typical_easy_pace = Column(String(50), nullable=True)
    video_retention_preference = Column(Boolean, default=False, nullable=False)
    optional_profile_preferences = Column(JSON, nullable=True)

    # Personal Goal settings
    goal_type = Column(String(50), nullable=True) # e.g. "IMPROVE_EFFICIENCY", "IMPROVE_CADENCE", etc.
    goal_description = Column(String(255), nullable=True)
    goal_status = Column(String(20), default="ACTIVE", nullable=True) # "ACTIVE", "COMPLETED", "PAUSED"
    goal_created_at = Column(DateTime(timezone=True), nullable=True)
    goal_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="profile")


class Analysis(Base):
    """Historical running session biomechanical analysis record."""
    __tablename__ = "analyses"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    video_id = Column(String(100), nullable=False)
    status = Column(String(50), default="completed", nullable=False)
    
    # Primary extracted biomechanical summary
    cadence_spm = Column(Float, nullable=True)
    step_count = Column(Integer, nullable=True)
    left_right_symmetry_pct = Column(Float, nullable=True)
    trunk_lean_deg = Column(Float, nullable=True)
    foot_strike_pattern = Column(String(50), nullable=True)
    overstride_risk = Column(String(100), nullable=True)
    relative_vertical_movement_proxy = Column(Float, nullable=True)
    form_classification = Column(String(150), nullable=True)
    overall_confidence = Column(String(50), nullable=True)
    form_consistency_score = Column(Float, nullable=True)

    # Detailed payloads
    raw_payload_json = Column(JSON, nullable=True)
    video_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="analyses")
    metrics = relationship("AnalysisMetric", back_populates="analysis", cascade="all, delete-orphan")
    observations = relationship("AnalysisObservation", back_populates="analysis", cascade="all, delete-orphan")


class AnalysisMetric(Base):
    """Normalized metric rows per analysis for historical querying & trending."""
    __tablename__ = "analysis_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(64), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_key = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    value = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)
    confidence = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    analysis = relationship("Analysis", back_populates="metrics")


class AnalysisObservation(Base):
    """Normalized observational insights per analysis."""
    __tablename__ = "analysis_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(64), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False) # e.g. "positive", "monitor", "info"
    observation = Column(Text, nullable=False)
    confidence = Column(String(50), nullable=True)
    recommended_action = Column(Text, nullable=True)
    why_flagged = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    analysis = relationship("Analysis", back_populates="observations")
