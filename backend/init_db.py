#!/usr/bin/env python3
"""
Database Initialization Script for Privacy-Preserving Adaptive Insider Threat Detection.
Executes table creation using SQLAlchemy models for MySQL.
"""

import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import test_connection, create_all_tables, db
from config import Config
import models  # Register models

def run_database_init():
    app = create_app()
    with app.app_context():
        db_info = Config.get_db_info()
        print("=" * 70)
        print(" MySQL Database Initialization: Insider Threat Detection System")
        print("=" * 70)
        print(f" Dialect:       {db_info['dialect']} (via {db_info['driver']})")
        print(f" Target Host:   {db_info['host']}:{db_info['port']}")
        print(f" Database Name: {db_info['database']}")
        print(f" Database User: {db_info['user']}")
        print(f" Password Set:  {'Yes' if db_info['has_password'] else 'No (empty)'}")
        print("-" * 70)

        print("[*] Testing connection to MySQL...")
        conn_status = test_connection()

        if conn_status["connected"]:
            print("[+] Connection SUCCESSFUL! Creating MySQL tables...")
            result = create_all_tables(app)
            if result["success"]:
                print("[+] All tables successfully initialized:")
                for table in result["tables"]:
                    print(f"    - {table}")
                print("=" * 70)
                return 0
            else:
                print(f"[-] Table creation failed: {result['error']}")
                return 1
        else:
            print("[-] MySQL connection check returned:")
            print(f"    Status:  {conn_status['status']}")
            print(f"    Message: {conn_status['message']}")
            print(f"    Error:   {conn_status['error']}")
            print("-" * 70)
            print("[!] CONFIGURATION REQUIRED:")
            print("    1. Ensure MySQL server is running (e.g., sudo systemctl start mysql)")
            print("    2. Create the target database in MySQL:")
            print(f"       CREATE DATABASE IF NOT EXISTS `{db_info['database']}` CHARACTER SET utf8mb4;")
            print("    3. Create the user and grant privileges:")
            print(f"       CREATE USER IF NOT EXISTS '{db_info['user']}'@'%' IDENTIFIED BY 'your_password';")
            print(f"       GRANT ALL PRIVILEGES ON `{db_info['database']}`.* TO '{db_info['user']}'@'%';")
            print("       FLUSH PRIVILEGES;")
            print("    4. Update .env with:")
            print(f"       DB_HOST={db_info['host']}")
            print(f"       DB_PORT={db_info['port']}")
            print(f"       DB_NAME={db_info['database']}")
            print(f"       DB_USER={db_info['user']}")
            print("       DB_PASSWORD=your_password")
            print("=" * 70)
            return 2

if __name__ == "__main__":
    sys.exit(run_database_init())
