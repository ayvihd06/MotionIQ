from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.storage import storage_manager
from app.db.session import SessionLocal
from app.db.models import Analysis, AnalysisMetric, AnalysisObservation

logger = logging.getLogger(__name__)

class IAnalysisRepository(ABC):
    """Abstract interface for analysis persistence and user data isolation."""

    @abstractmethod
    def save_analysis(self, analysis_id: str, data: Dict[str, Any], user_id: Optional[str] = None) -> None:
        """Persists an analysis record, its metrics, and observations."""
        pass

    @abstractmethod
    def get_analysis(self, analysis_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves an analysis record by ID with ownership verification."""
        pass

    @abstractmethod
    def list_analyses(self, limit: int = 20, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists recent analyses for the authenticated user (strict data isolation)."""
        pass

    @abstractmethod
    def delete_analysis(self, analysis_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes an analysis record, its relations, and associated artifacts."""
        pass


class PostgresAnalysisRepository(IAnalysisRepository):
    """PostgreSQL-backed analysis repository with automatic local JSON mirror and strict user isolation."""

    def save_analysis(self, analysis_id: str, data: Dict[str, Any], user_id: Optional[str] = None) -> None:
        # 1. Mirror to local JSON for filesystem compatibility
        storage_manager.save_analysis_json(analysis_id, data)

        # 2. Persist to PostgreSQL relational database
        db: Session = SessionLocal()
        try:
            effective_user_id = user_id or data.get("user_id")
            
            # Check for existing analysis record
            existing = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if existing:
                analysis = existing
                analysis.status = data.get("status", "completed")
            else:
                analysis = Analysis(
                    id=analysis_id,
                    user_id=effective_user_id,
                    video_id=data.get("video_id", ""),
                    status=data.get("status", "completed")
                )
                db.add(analysis)

            # Update primary telemetry fields
            analysis.cadence_spm = data.get("cadence_spm")
            analysis.step_count = data.get("step_count")
            analysis.left_right_symmetry_pct = data.get("left_right_symmetry_pct")
            analysis.trunk_lean_deg = data.get("trunk_lean_deg")
            analysis.foot_strike_pattern = data.get("foot_strike_pattern")
            analysis.overstride_risk = data.get("overstride_risk")
            analysis.relative_vertical_movement_proxy = data.get("relative_vertical_movement_proxy")
            analysis.form_classification = data.get("form_classification")
            analysis.overall_confidence = data.get("overall_confidence")
            
            overall_summary = data.get("overall_summary") or {}
            analysis.form_consistency_score = overall_summary.get("form_consistency_score")
            analysis.raw_payload_json = data
            analysis.video_metadata = data.get("video_metadata")

            # Remove old metric and observation rows if updating
            if existing:
                db.query(AnalysisMetric).filter(AnalysisMetric.analysis_id == analysis_id).delete()
                db.query(AnalysisObservation).filter(AnalysisObservation.analysis_id == analysis_id).delete()

            # Insert normalized metrics
            for m in data.get("metrics_breakdown", []):
                metric_row = AnalysisMetric(
                    analysis_id=analysis_id,
                    metric_key=m.get("key", m.get("name", "metric")),
                    name=m.get("name", ""),
                    value=str(m.get("value", "")),
                    unit=m.get("unit", ""),
                    confidence=m.get("confidence"),
                    status=m.get("status"),
                    description=m.get("description")
                )
                db.add(metric_row)

            # Insert normalized observations / insights
            for ins in data.get("context_insights", []):
                obs_row = AnalysisObservation(
                    analysis_id=analysis_id,
                    title=ins.get("title", ""),
                    category=ins.get("category", ""),
                    severity=ins.get("severity", "info"),
                    observation=ins.get("description", ""),
                    confidence=ins.get("confidence"),
                    recommended_action=ins.get("recommended_action"),
                    why_flagged=ins.get("why_flagged")
                )
                db.add(obs_row)

            db.commit()
            logger.info(f"PostgreSQL: Analysis {analysis_id} successfully persisted.")
        except Exception as e:
            db.rollback()
            logger.error(f"PostgreSQL persistence error for analysis {analysis_id}: {e}")
        finally:
            db.close()

    def get_analysis(self, analysis_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # Demo session is always accessible
        is_demo = (analysis_id == "demo-runner-session-001")

        # 1. Attempt PostgreSQL retrieval
        db: Session = SessionLocal()
        try:
            query = db.query(Analysis).filter(Analysis.id == analysis_id)
            record = query.first()
            if record:
                # Enforce strict ownership if not public demo
                if not is_demo:
                    if record.user_id and record.user_id != user_id:
                        return None
                    if not record.user_id and user_id is not None:
                        # Guest analysis cannot be claimed or accessed by a different authenticated context
                        return None

                if record.raw_payload_json:
                    return record.raw_payload_json
        except Exception as e:
            logger.warning(f"PostgreSQL retrieval warning for {analysis_id}: {e}")
        finally:
            db.close()

        # 2. Fallback to local JSON storage
        json_data = storage_manager.get_analysis_json(analysis_id)
        if json_data:
            if not is_demo:
                rec_user_id = json_data.get("user_id")
                if rec_user_id and rec_user_id != user_id:
                    return None
                if not rec_user_id and user_id is not None:
                    return None
            return json_data

        return None

    def list_analyses(self, limit: int = 20, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        db: Session = SessionLocal()
        try:
            query = db.query(Analysis)
            # Strict User Isolation: Authenticated runners see ONLY their own records
            if user_id:
                query = query.filter(Analysis.user_id == user_id)
            else:
                # Unauthenticated guests see only guest analyses (or empty if none)
                query = query.filter(Analysis.user_id == None)
            
            records = query.order_by(Analysis.created_at.desc()).limit(limit).all()
            if records:
                return [
                    {
                        "analysis_id": r.id,
                        "user_id": r.user_id,
                        "video_id": r.video_id,
                        "created_at": r.created_at.isoformat() if r.created_at else "",
                        "status": r.status,
                        "cadence_spm": r.cadence_spm or 0.0,
                        "left_right_symmetry_pct": r.left_right_symmetry_pct or 0.0,
                        "form_classification": r.form_classification or "Running Form Analysis",
                        "overall_confidence": r.overall_confidence or "High",
                        "form_consistency_score": r.form_consistency_score or 85.0
                    }
                    for r in records
                ]
            else:
                return []
        except Exception as e:
            logger.warning(f"PostgreSQL list_analyses error: {e}. Falling back to filesystem.")
        finally:
            db.close()

        # Filesystem fallback
        analyses_dir = storage_manager.analyses_dir
        if not analyses_dir.exists():
            return []

        results = []
        for file_path in sorted(analyses_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rec_user_id = data.get("user_id")
                    if user_id:
                        if rec_user_id != user_id:
                            continue
                    else:
                        if rec_user_id is not None:
                            continue
                    
                    summary = {
                        "analysis_id": data.get("analysis_id", file_path.stem),
                        "user_id": data.get("user_id"),
                        "video_id": data.get("video_id", ""),
                        "created_at": data.get("created_at", ""),
                        "status": data.get("status", "completed"),
                        "cadence_spm": data.get("cadence_spm", 0.0),
                        "left_right_symmetry_pct": data.get("left_right_symmetry_pct", 0.0),
                        "form_classification": data.get("form_classification", "Running Form Analysis"),
                        "overall_confidence": data.get("overall_confidence", "High"),
                        "form_consistency_score": (data.get("overall_summary") or {}).get("form_consistency_score", 85.0)
                    }
                    results.append(summary)
                    if len(results) >= limit:
                        break
            except Exception:
                continue

        return results

    def delete_analysis(self, analysis_id: str, user_id: Optional[str] = None) -> bool:
        # 1. Delete from PostgreSQL with strict user isolation
        db: Session = SessionLocal()
        deleted_from_db = False
        try:
            query = db.query(Analysis).filter(Analysis.id == analysis_id)
            if user_id:
                query = query.filter(Analysis.user_id == user_id)
            
            analysis = query.first()
            if analysis:
                db.delete(analysis)
                db.commit()
                deleted_from_db = True
            elif user_id:
                # If user_id was provided and not found in their records, access is denied
                return False
        except Exception as e:
            db.rollback()
            logger.error(f"PostgreSQL delete error for {analysis_id}: {e}")
        finally:
            db.close()

        # 2. Delete local JSON file and annotated video if owner or unauthenticated
        path = storage_manager.get_analysis_path(analysis_id)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                if user_id and json_data.get("user_id") and json_data.get("user_id") != user_id:
                    return False
                path.unlink(missing_ok=True)
                deleted_from_db = True
            except Exception:
                pass

        if deleted_from_db:
            storage_manager.cleanup_annotated_video(analysis_id)
        return deleted_from_db

# Default repository instance
analysis_repository: IAnalysisRepository = PostgresAnalysisRepository()
