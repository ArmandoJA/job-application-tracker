"""Database connection helpers for the Job Application Tracker.

Connection settings come from environment variables so nobody has to edit
code (or commit a password). Defaults match a local MySQL server.
"""
import os
import mysql.connector

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "3307")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "job_tracker"),
}


def get_db():
    """Open a new connection to the job_tracker database."""
    return mysql.connector.connect(**DB_CONFIG)


def query(sql, params=None, one=False):
    """Run a SELECT and return rows as dicts (or a single dict if one=True)."""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        return cursor.fetchone() if one else cursor.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE, commit, and return the new row id."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
