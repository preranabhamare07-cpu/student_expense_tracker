"""
database.py
-----------
Handles all SQLite persistence for the Student Expense Tracker.

Responsibilities:
  - Create and migrate the database schema (expenses, settings tables).
  - Provide CRUD helpers for expenses.
  - Provide get/set helpers for the monthly allowance setting.
  - Use parameterised queries exclusively — no string interpolation.
"""

import sqlite3
from datetime import date
from pathlib import Path

# ── Path ──────────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "expenses.db"

# ── Supported categories & payment methods ────────────────────────────────────
CATEGORIES = [
    "Food",
    "Travel",
    "Education",
    "Shopping",
    "Entertainment",
    "Bills",
    "Other",
]

PAYMENT_METHODS = [
    "Cash",
    "UPI",
    "Debit Card",
    "Credit Card",
    "Net Banking",
    "Other",
]

DATE_FORMAT = "%Y-%m-%d"  # ISO-8601 — consistent across the whole app


# ── Connection helper ─────────────────────────────────────────────────────────
def _get_connection() -> sqlite3.Connection:
    """Return a connection with Row factory so columns are accessible by name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enforce foreign-key constraints and WAL mode for better concurrency.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ── Schema initialisation ─────────────────────────────────────────────────────
def init_db() -> None:
    """
    Create the database tables if they do not already exist.
    Call this once at application start-up (app.py).
    """
    with _get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                date           TEXT    NOT NULL,          -- ISO-8601 YYYY-MM-DD
                amount         REAL    NOT NULL,          -- always positive
                category       TEXT    NOT NULL,
                payment_method TEXT    NOT NULL,
                notes          TEXT    DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            -- Seed a default allowance of 0 so the setting always exists.
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('monthly_allowance', '0');
            """
        )


# ── Expense CRUD ──────────────────────────────────────────────────────────────
def add_expense(
    expense_date: date,
    amount: float,
    category: str,
    payment_method: str,
    notes: str = "",
) -> int:
    """
    Insert a new expense row.

    Parameters
    ----------
    expense_date   : Python date object — stored as ISO-8601 string.
    amount         : Positive float (validation must be done by the caller).
    category       : One of CATEGORIES.
    payment_method : One of PAYMENT_METHODS.
    notes          : Optional free-text note.

    Returns
    -------
    The auto-generated integer ID of the new row.
    """
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Choose from {CATEGORIES}.")
    if payment_method not in PAYMENT_METHODS:
        raise ValueError(
            f"Invalid payment method '{payment_method}'. Choose from {PAYMENT_METHODS}."
        )
    if amount <= 0:
        raise ValueError("Amount must be a positive number.")

    date_str = expense_date.strftime(DATE_FORMAT)

    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO expenses (date, amount, category, payment_method, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date_str, float(amount), category, payment_method, notes.strip()),
        )
        return cursor.lastrowid


def get_all_expenses() -> list[dict]:
    """
    Return every expense row as a list of plain dicts, newest-first.
    """
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM expenses ORDER BY date DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_expenses_by_month(year: int, month: int) -> list[dict]:
    """
    Return expenses for a specific calendar month.
    Uses a date-range filter so the query stays index-friendly.
    """
    from calendar import monthrange

    last_day = monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-{last_day:02d}"

    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC, id DESC
            """,
            (start, end),
        ).fetchall()
    return [dict(row) for row in rows]


def update_expense(
    expense_id: int,
    expense_date: date,
    amount: float,
    category: str,
    payment_method: str,
    notes: str = "",
) -> bool:
    """
    Update an existing expense by its ID.

    Returns True if a row was updated, False if the ID was not found.
    """
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category '{category}'.")
    if payment_method not in PAYMENT_METHODS:
        raise ValueError(f"Invalid payment method '{payment_method}'.")
    if amount <= 0:
        raise ValueError("Amount must be a positive number.")

    date_str = expense_date.strftime(DATE_FORMAT)

    with _get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE expenses
            SET date=?, amount=?, category=?, payment_method=?, notes=?
            WHERE id=?
            """,
            (date_str, float(amount), category, payment_method, notes.strip(), expense_id),
        )
        return cursor.rowcount > 0


def delete_expense(expense_id: int) -> bool:
    """
    Delete an expense by ID.

    Returns True if deleted, False if not found.
    """
    with _get_connection() as conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        return cursor.rowcount > 0


# ── Settings helpers ──────────────────────────────────────────────────────────
def get_monthly_allowance() -> float:
    """Return the stored monthly allowance (defaults to 0.0)."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key='monthly_allowance'"
        ).fetchone()
    return float(row["value"]) if row else 0.0


def set_monthly_allowance(amount: float) -> None:
    """
    Upsert the monthly allowance setting.

    Raises ValueError for non-positive amounts.
    """
    if amount < 0:
        raise ValueError("Allowance cannot be negative.")
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES ('monthly_allowance', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (str(float(amount)),),
        )
