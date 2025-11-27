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


def insert_patient(
    first_name: str,
    last_name: str,
    birth_date: str,
    age_group: str,
    gender: str,
    phone: str,
    email: str,
    address: str | None = None,
) -> Tuple[bool, str]:
    """Insert a patient row into patients table with current timestamp."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}"

    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO patients (first_name, last_name, birth_date, age_group, gender, phone, email, address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (first_name, last_name, birth_date, age_group, gender, phone, email, address),
        )
        conn.commit()
        return True, "Patient added."
    except Error as exc:
        return False, f"Insert failed: {exc}"
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


def insert_appointment(
    patient_id: int,
    dentist_id: int,
    scheduled_at: str,
    status: str,
    reason: str,
    notes: str | None = None,
    created_at: str | None = None,
) -> Tuple[bool, str, Optional[int]]:
    """Insert a new appointment row and return its id."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}", None

    try:
        cur = conn.cursor()
        if created_at:
            cur.execute(
                """
                INSERT INTO appointments (patient_id, dentist_id, scheduled_at, status, reason, notes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (patient_id, dentist_id, scheduled_at, status, reason, notes, created_at),
            )
        else:
            cur.execute(
                """
                INSERT INTO appointments (patient_id, dentist_id, scheduled_at, status, reason, notes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (patient_id, dentist_id, scheduled_at, status, reason, notes),
            )
        appt_id = cur.lastrowid
        conn.commit()
        return True, "Appointment recorded.", appt_id
    except Error as exc:
        return False, f"Insert failed: {exc}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def insert_payment(
    appointment_id: int,
    patient_id: int,
    amount: float,
    method: str,
    status: str,
    reference_no: str | None = None,
    remarks: str | None = None,
    payment_date: str | None = None,
) -> Tuple[bool, str]:
    """Insert a new payment row."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}"

    try:
        cur = conn.cursor()
        if payment_date:
            cur.execute(
                """
                INSERT INTO payments (appointment_id, patient_id, amount, payment_date, method, status, reference_no, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (appointment_id, patient_id, amount, payment_date, method, status, reference_no, remarks),
            )
        else:
            cur.execute(
                """
                INSERT INTO payments (appointment_id, patient_id, amount, payment_date, method, status, reference_no, remarks)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s)
                """,
                (appointment_id, patient_id, amount, method, status, reference_no, remarks),
            )
        conn.commit()
        return True, "Payment recorded."
    except Error as exc:
        return False, f"Insert failed: {exc}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def insert_patient_history(
    patient_id: int,
    appointment_id: int,
    visit_date: str,
    diagnosis: str | None = None,
    treatment_given: str | None = None,
    prescription: str | None = None,
    follow_up_date: str | None = None,
    notes: str | None = None,
) -> Tuple[bool, str]:
    """Insert a row into patient_history table."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}"

    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO patient_history
            (patient_id, appointment_id, visit_date, diagnosis, treatment_given, prescription, follow_up_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (patient_id, appointment_id, visit_date, diagnosis, treatment_given, prescription, follow_up_date, notes),
        )
        conn.commit()
        return True, "Patient history saved."
    except Error as exc:
        return False, f"Insert failed: {exc}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_patient_history() -> Tuple[bool, str, Optional[list[dict]]]:
    """Return all rows from patient_history table."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}", None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM patient_history")
        rows = cur.fetchall() or []
        return True, "ok", rows
    except Error as exc:
        return False, f"Query failed: {exc}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_payments() -> Tuple[bool, str, Optional[list[dict]]]:
    """Return all rows from payments table."""
    try:
        conn = get_connection()
    except Error as exc:
        return False, f"DB connection failed: {exc}", None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM payments")
        rows = cur.fetchall() or []
        return True, "ok", rows
    except Error as exc:
        return False, f"Query failed: {exc}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass
