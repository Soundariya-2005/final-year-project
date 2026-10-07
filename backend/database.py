"""
Database Module for Privacy-Preserving Adaptive Insider Threat Detection.
Initializes SQLAlchemy instance, table creation helpers, and connection testing.
"""

import sys
from typing import Dict, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Instantiate the SQLAlchemy object
db = SQLAlchemy()

def init_db(app):
    """Binds the SQLAlchemy extension to the Flask application."""
    db.init_app(app)

def test_connection() -> Dict[str, Any]:
    """
    Tests connectivity to the configured MySQL database.
    Performs a lightweight 'SELECT 1;' query with safe error capturing.
    Does not crash the application if MySQL is unreachable.
    """
    try:
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1;"))
            row = result.fetchone()
            if row and row[0] == 1:
                return {
                    "connected": True,
                    "status": "healthy",
                    "message": "Successfully connected to MySQL database",
                    "error": None,
                }
            return {
                "connected": False,
                "status": "unexpected_result",
                "message": "Query executed but returned unexpected payload",
                "error": None,
            }
    except OperationalError as oe:
        # Common MySQL operational errors (e.g. host unreachable, wrong password, db not found)
        err_msg = str(oe.orig) if hasattr(oe, "orig") else str(oe)
        return {
            "connected": False,
            "status": "connection_failed",
            "message": "Cannot reach MySQL server. Check DB_HOST, DB_PORT, and credentials in .env.",
            "error": err_msg,
        }
    except SQLAlchemyError as se:
        return {
            "connected": False,
            "status": "sqlalchemy_error",
            "message": "Database query error",
            "error": str(se),
        }
    except Exception as ex:
        return {
            "connected": False,
            "status": "unknown_error",
            "message": "Unexpected error while testing MySQL connection",
            "error": str(ex),
        }

def create_all_tables(app) -> Dict[str, Any]:
    """
    Creates all defined MySQL schema tables if they do not already exist.
    Must be called within an application context.
    """
    with app.app_context():
        # Import models so metadata is registered with SQLAlchemy
        import models  # noqa: F401
        try:
            db.create_all()
            return {
                "success": True,
                "message": "All MySQL tables created or verified successfully",
                "tables": list(db.metadata.tables.keys()),
            }
        except Exception as e:
            err_msg = str(e)
            return {
                "success": False,
                "message": "Failed to create MySQL tables",
                "error": err_msg,
                "tables": list(db.metadata.tables.keys()),
            }


if __name__ == "__main__":
    # Allows running standalone: python3 backend/database.py
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app import create_app

    flask_app = create_app()
    with flask_app.app_context():
        print("[*] Testing MySQL connection...")
        status = test_connection()
        print(f"[*] Connection status: {status}")

        if status["connected"]:
            print("[*] Creating database tables...")
            create_result = create_all_tables(flask_app)
            print(f"[*] Table creation result: {create_result}")
        else:
            print("[!] MySQL server is not currently reachable.")
            print("    Please verify DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD in .env.")
