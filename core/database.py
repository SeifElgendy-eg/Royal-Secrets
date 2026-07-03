"""
Registration storage.

Uses a local SQLite database (no server, no extra dependencies) so the
quiz app can run standalone on event-day, then export everything to CSV
once the event is over.
"""

import csv
import os
import sqlite3
import sys
from datetime import datetime, timezone

# data/registrations.db lives next to the app so registrations survive
# between runs. When running from source that's the project root (one
# level up from core/). When frozen by PyInstaller, __file__ resolves
# inside the temp _MEIPASS extraction folder instead, which is wiped
# after the app closes — so in that case anchor to the real exe's own
# folder instead, so the data directory persists alongside it.
if getattr(sys, "frozen", False):
    _APP_ROOT = os.path.dirname(os.path.abspath(sys.executable))
else:
    _APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(_APP_ROOT, "data", "registrations.db")


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create the registrations table if it doesn't exist yet, and migrate
    older databases (created before the email field existed) by adding the
    column in place. Safe to call every time the app starts."""
    conn = _get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                mobile        TEXT NOT NULL UNIQUE,
                email         TEXT NOT NULL DEFAULT '',
                area          TEXT NOT NULL,
                registered_at TEXT NOT NULL
            )
            """
        )

        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(registrations)")}
        if "email" not in existing_columns:
            # Pre-email database (e.g. registrations.db from before this
            # feature) — add the column so old rows keep working, they'll
            # just show an empty email until re-registered.
            conn.execute("ALTER TABLE registrations ADD COLUMN email TEXT NOT NULL DEFAULT ''")

        conn.commit()
    finally:
        conn.close()


def insert_registration(name: str, mobile: str, email: str, area: str) -> tuple[bool, str | None]:
    """Insert a new registration.

    Mobile numbers are unique, so the same player can't register twice on
    the same device. Returns (success, error_message) — error_message is
    None on success and a user-facing string on failure, matching what
    main.py already expects.
    """
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO registrations (name, mobile, email, area, registered_at) VALUES (?, ?, ?, ?, ?)",
            (name, mobile, email, area, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "This mobile number is already registered."
    except sqlite3.Error as exc:
        return False, f"Database error: {exc}"
    finally:
        conn.close()


def fetch_all_registrations() -> list[tuple]:
    """Return every registration as (id, name, mobile, email, area,
    registered_at), oldest first."""
    conn = _get_connection()
    try:
        cur = conn.execute(
            "SELECT id, name, mobile, email, area, registered_at FROM registrations ORDER BY id"
        )
        return cur.fetchall()
    finally:
        conn.close()


def registration_count() -> int:
    conn = _get_connection()
    try:
        cur = conn.execute("SELECT COUNT(*) FROM registrations")
        return cur.fetchone()[0]
    finally:
        conn.close()


def export_to_csv(output_path: str) -> tuple[bool, str]:
    """Dump every registration to a CSV file at output_path.

    Returns (success, message): on success `message` is the path written,
    on failure it's a human-readable error to show the organizer.
    """
    try:
        rows = fetch_all_registrations()
        out_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Mobile", "Email", "Area", "Registered At (UTC)"])
            writer.writerows(rows)
        return True, output_path
    except OSError as exc:
        return False, f"Could not write CSV file: {exc}"