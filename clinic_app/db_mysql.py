from __future__ import annotations

import os
from typing import Optional, Tuple

import mysql.connector
from mysql.connector import Error


def get_connection():
    """Return a MySQL connection using environment variables for config."""
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        # Default to dental_clinic database; override with DB_NAME env var.
        "database": os.getenv("DB_NAME", "dental_clinic"),
    }
    return mysql.connector.connect(**config)


def verify_user(username: str, password: str) -> Tuple[bool, str, Optional[str]]:
    """
    Check username/password against user_accounts table.
    Returns (ok, message, role). Message is user-friendly.
    """
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}", None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT username, password_hash, role, status
            FROM user_accounts
            WHERE username = %s
            LIMIT 1
            """,
            (username,),
        )
        row = cursor.fetchone()
        if row is None:
            return False, "Invalid username or password.", None

        if row.get("status", "").lower() not in ("active", "1", "true", "yes"):
            return False, "Account is not active.", None

        stored_value = (row.get("password_hash") or "").strip()
        # Direct comparison without bcrypt hashing; trim DB value to avoid trailing CR/LF from manual edits.
        if password != stored_value:
            return False, "Invalid username or password.", None

        return True, "Login successful.", row.get("role")
    except Error as exc:
        return False, f"Query failed: {exc}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_patients() -> Tuple[bool, str, Optional[list[dict]]]:
    """Return all rows from patients table."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}", None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM patients")
        rows = cur.fetchall() or []
        return True, "ok", rows
    except Error as exc:
        return False, f"Query failed: {exc}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_treatments() -> Tuple[bool, str, Optional[list[dict]]]:
    """Return all rows from treatments table."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}", None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM treatments")
        rows = cur.fetchall() or []
        return True, "ok", rows
    except Error as exc:
        return False, f"Query failed: {exc}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_appointments() -> Tuple[bool, str, Optional[list[dict]]]:
    """Return all rows from appointments table."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}", None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM appointments")
        rows = cur.fetchall() or []
        return True, "ok", rows
    except Error as exc:
        return False, f"Query failed: {exc}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_dentists() -> Tuple[bool, str, Optional[list[dict]]]:
    """Return all rows from dentists table."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}", None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM dentists")
        rows = cur.fetchall() or []
        return True, "ok", rows
    except Error as exc:
        return False, f"Query failed: {exc}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass
