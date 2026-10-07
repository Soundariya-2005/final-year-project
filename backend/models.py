"""
SQLAlchemy Domain Models for Privacy-Preserving Adaptive Insider Threat Detection.

Defines schemas for:
1. users
2. activity_logs
3. behavior_features
4. anomaly_results
5. risk_scores
6. risk_explanations
7. analysis_runs
8. settings
"""

from datetime import datetime, timezone
import json
from database import db

def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    """
    User entity with privacy-preserving pseudonymous identifiers.
    Protects employee identities through pseudonymization and hashing.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pseudonymous_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    original_id_hash = db.Column(db.String(128), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    activity_logs = db.relationship("ActivityLog", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    behavior_features = db.relationship("BehaviorFeature", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    anomaly_results = db.relationship("AnomalyResult", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    risk_scores = db.relationship("RiskScore", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    risk_explanations = db.relationship("RiskExplanation", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "pseudonymous_id": self.pseudonymous_id,
            "original_id_hash": self.original_id_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ActivityLog(db.Model):
    """
    Raw or aggregated employee activity events (e.g. login, file access, email).
    """
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_date = db.Column(db.Date, nullable=False, index=True)
    activity_data = db.Column(db.Text, nullable=True)  # Stores JSON string of event metadata
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        parsed_data = None
        if self.activity_data:
            try:
                parsed_data = json.loads(self.activity_data)
            except Exception:
                parsed_data = self.activity_data

        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_date": self.activity_date.isoformat() if self.activity_date else None,
            "activity_data": parsed_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BehaviorFeature(db.Model):
    """
    Engineered behavioral feature vector aggregated per user per day.
    Used as input for adaptive anomaly detection.
    """
    __tablename__ = "behavior_features"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_date = db.Column(db.Date, nullable=False, index=True)
    login_count = db.Column(db.Integer, default=0, nullable=False)
    after_hours_login = db.Column(db.Integer, default=0, nullable=False)
    file_access_count = db.Column(db.Integer, default=0, nullable=False)
    sensitive_file_access = db.Column(db.Integer, default=0, nullable=False)
    email_count = db.Column(db.Integer, default=0, nullable=False)
    external_email_count = db.Column(db.Integer, default=0, nullable=False)
    web_upload_volume = db.Column(db.Float, default=0.0, nullable=False)  # in Megabytes
    average_session_minutes = db.Column(db.Float, default=0.0, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_date": self.activity_date.isoformat() if self.activity_date else None,
            "login_count": self.login_count,
            "after_hours_login": self.after_hours_login,
            "file_access_count": self.file_access_count,
            "sensitive_file_access": self.sensitive_file_access,
            "email_count": self.email_count,
            "external_email_count": self.external_email_count,
            "web_upload_volume": self.web_upload_volume,
            "average_session_minutes": self.average_session_minutes,
        }


class AnomalyResult(db.Model):
    """
    Outputs from the Isolation Forest anomaly detection engine.
    """
    __tablename__ = "anomaly_results"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_date = db.Column(db.Date, nullable=False, index=True)
    anomaly_score = db.Column(db.Float, nullable=False)
    anomaly_flag = db.Column(db.Boolean, default=False, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_date": self.activity_date.isoformat() if self.activity_date else None,
            "anomaly_score": self.anomaly_score,
            "anomaly_flag": self.anomaly_flag,
        }


class RiskScore(db.Model):
    """
    Cumulative adaptive risk score and classification level for early warning.
    """
    __tablename__ = "risk_scores"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_date = db.Column(db.Date, nullable=False, index=True)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(32), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_date": self.activity_date.isoformat() if self.activity_date else None,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
        }


class RiskExplanation(db.Model):
    """
    SHAP-based feature-level attribution explaining why a specific user/event was flagged.
    """
    __tablename__ = "risk_explanations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_date = db.Column(db.Date, nullable=False, index=True)
    feature = db.Column(db.String(128), nullable=False)
    contribution = db.Column(db.Float, nullable=False)
    direction = db.Column(db.String(32), nullable=False)  # INCREASES_RISK, DECREASES_RISK

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_date": self.activity_date.isoformat() if self.activity_date else None,
            "feature": self.feature,
            "contribution": self.contribution,
            "direction": self.direction,
        }


class AnalysisRun(db.Model):
    """
    Tracks metadata and parameters of batch detection runs and dataset imports.
    """
    __tablename__ = "analysis_runs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=True)
    record_count = db.Column(db.Integer, default=0, nullable=False)
    user_count = db.Column(db.Integer, default=0, nullable=False)
    parameters = db.Column(db.Text, nullable=True)  # JSON formatted parameters
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        parsed_params = None
        if self.parameters:
            try:
                parsed_params = json.loads(self.parameters)
            except Exception:
                parsed_params = self.parameters

        return {
            "id": self.id,
            "filename": self.filename,
            "record_count": self.record_count,
            "user_count": self.user_count,
            "parameters": parsed_params,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Setting(db.Model):
    """
    System hyper-parameters for anomaly thresholding and adaptive risk progression.
    """
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alpha = db.Column(db.Float, default=0.05, nullable=False)
    contamination = db.Column(db.Float, default=0.05, nullable=False)
    risk_decay = db.Column(db.Float, default=0.1, nullable=False)
    risk_gain = db.Column(db.Float, default=0.3, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "alpha": self.alpha,
            "contamination": self.contamination,
            "risk_decay": self.risk_decay,
            "risk_gain": self.risk_gain,
        }
