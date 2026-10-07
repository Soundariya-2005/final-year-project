"""
Machine Learning, Feature Engineering, Adaptive Profiling, Anomaly Detection,
Progressive Risk, and SHAP Explainability Package.
"""

from .feature_engineering import (
    extract_behavior_features,
    save_features_to_mysql,
    REQUIRED_FEATURE_COLUMNS,
)
from .adaptive_profile import (
    calculate_adaptive_profile,
    get_user_profile_summary,
    DEFAULT_ALPHA,
    BEHAVIORAL_FEATURES,
    get_default_alpha_from_settings,
)
from .anomaly_detection import (
    detect_anomalies,
    save_anomaly_results_to_mysql,
    get_anomaly_summary,
    DEFAULT_CONTAMINATION,
)
from .risk_engine import (
    calculate_progressive_risk,
    save_risk_scores_to_mysql,
    get_risk_summary,
    DEFAULT_RISK_DECAY,
    DEFAULT_RISK_GAIN,
    RISK_THRESHOLDS,
)
from .explainability import (
    explain_anomalies_shap,
    get_user_explanations,
    save_explanations_to_mysql,
)

__all__ = [
    "extract_behavior_features",
    "save_features_to_mysql",
    "REQUIRED_FEATURE_COLUMNS",
    "calculate_adaptive_profile",
    "get_user_profile_summary",
    "DEFAULT_ALPHA",
    "BEHAVIORAL_FEATURES",
    "get_default_alpha_from_settings",
    "detect_anomalies",
    "save_anomaly_results_to_mysql",
    "get_anomaly_summary",
    "DEFAULT_CONTAMINATION",
    "calculate_progressive_risk",
    "save_risk_scores_to_mysql",
    "get_risk_summary",
    "DEFAULT_RISK_DECAY",
    "DEFAULT_RISK_GAIN",
    "RISK_THRESHOLDS",
    "explain_anomalies_shap",
    "get_user_explanations",
    "save_explanations_to_mysql",
]
