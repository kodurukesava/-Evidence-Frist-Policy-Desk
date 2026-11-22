
import sqlite3

from backend.app.database import DATABASE_FILE


def migrate_document_lifecycle():
    connection = sqlite3.connect(str(DATABASE_FILE))

    try:
        cursor = connection.cursor()

        columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(documents)"
            ).fetchall()
        }

        migrations = {
            "lifecycle_status": (
                "ALTER TABLE documents "
                "ADD COLUMN lifecycle_status "
                "VARCHAR(20) NOT NULL DEFAULT 'active'"
            ),
            "archived_at": (
                "ALTER TABLE documents "
                "ADD COLUMN archived_at DATETIME"
            ),
            "deleted_at": (
                "ALTER TABLE documents "
                "ADD COLUMN deleted_at DATETIME"
            ),
        }

        for column_name, sql in migrations.items():
            if column_name not in columns:
                cursor.execute(sql)
                print(f"Added column: {column_name}")
            else:
                print(f"Column already exists: {column_name}")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            ix_documents_lifecycle_status
            ON documents (lifecycle_status)
        """)

        connection.commit()
        print("Document lifecycle migration completed.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    migrate_document_lifecycle()
