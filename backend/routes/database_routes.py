"""
Database health, status, and schema routes.
Provides endpoints to test MySQL connectivity and initialize tables.
"""

from flask import Blueprint, jsonify, current_app
from database import test_connection, create_all_tables, db
from config import Config
import models  # Ensure all models are registered

db_bp = Blueprint("database", __name__, url_prefix="/api/database")

@db_bp.route("/status", methods=["GET"])
def database_status():
    """
    Checks MySQL connectivity and returns diagnostic configuration information.
    Does not crash if MySQL is offline.
    """
    conn_result = test_connection()
    db_info = Config.get_db_info()
    defined_tables = list(db.metadata.tables.keys())

    response_data = {
        "connected": conn_result["connected"],
        "status": conn_result["status"],
        "message": conn_result["message"],
        "error": conn_result["error"],
        "connection_details": db_info,
        "defined_models": [
            "User (users)",
            "ActivityLog (activity_logs)",
            "BehaviorFeature (behavior_features)",
            "AnomalyResult (anomaly_results)",
            "RiskScore (risk_scores)",
            "RiskExplanation (risk_explanations)",
            "AnalysisRun (analysis_runs)",
            "Setting (settings)",
        ],
        "schema_tables_defined": defined_tables,
        "configuration_guide": {
            "mysql_service_required": not conn_result["connected"],
            "target_url": f"mysql+pymysql://{db_info['user']}:****@{db_info['host']}:{db_info['port']}/{db_info['database']}",
            "hint": "Set DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD or DATABASE_URL in .env when MySQL is running."
        }
    }

    return jsonify(response_data), 200


@db_bp.route("/init", methods=["POST"])
def initialize_database():
    """
    Attempts to create all MySQL tables using SQLAlchemy db.create_all().
    """
    result = create_all_tables(current_app)
    status_code = 200 if result["success"] else 503
    return jsonify(result), status_code


@db_bp.route("/schema", methods=["GET"])
def database_schema():
    """
    Returns full metadata for the 8 required domain models.
    """
    schema = {}
    for table_name, table in db.metadata.tables.items():
        columns = []
        for col in table.columns:
            fk_list = [fk.target_fullname for fk in col.foreign_keys]
            columns.append({
                "name": col.name,
                "type": str(col.type),
                "primary_key": col.primary_key,
                "nullable": col.nullable,
                "foreign_keys": fk_list if fk_list else None,
            })
        schema[table_name] = columns

    return jsonify({
        "status": "ok",
        "total_tables": len(schema),
        "tables": schema,
    }), 200
