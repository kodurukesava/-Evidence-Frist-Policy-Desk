import sqlite3
from pathlib import Path

database_path = Path(__file__).resolve().parent / "data" / "database" / "evidence_desk.db"

if not database_path.exists():
    print("Database file not found:", database_path)
else:
    connection = sqlite3.connect(database_path)

    print("Integrity:", connection.execute("PRAGMA integrity_check").fetchone())

    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    print("Tables:", tables)

    connection.close()