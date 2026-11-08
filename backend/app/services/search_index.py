
from sqlalchemy import text

from ..database import engine


def initialize_search_index():
    """
    Create an FTS5 index for document segments
    and synchronize it with the SQLite table.
    """

    with engine.begin() as connection:

        # 1. Create the FTS5 virtual table
        connection.exec_driver_sql("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_segments_fts
            USING fts5(
                content,
                content='document_segments',
                content_rowid='id',
                tokenize='unicode61'
            )
        """)

        # 2. Automatically index newly inserted segments
        connection.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS document_segments_ai
            AFTER INSERT ON document_segments
            BEGIN
                INSERT INTO document_segments_fts(rowid, content)
                VALUES (new.id, new.content);
            END;
        """)

        # 3. Remove old indexed content when a segment is deleted
        connection.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS document_segments_ad
            AFTER DELETE ON document_segments
            BEGIN
                INSERT INTO document_segments_fts(
                    document_segments_fts,
                    rowid,
                    content
                )
                VALUES ('delete', old.id, old.content);
            END;
        """)

        # 4. Update the index when segment content changes
        connection.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS document_segments_au
            AFTER UPDATE ON document_segments
            BEGIN
                INSERT INTO document_segments_fts(
                    document_segments_fts,
                    rowid,
                    content
                )
                VALUES ('delete', old.id, old.content);

                INSERT INTO document_segments_fts(rowid, content)
                VALUES (new.id, new.content);
            END;
        """)

        # 5. Index all existing document segments
        connection.exec_driver_sql("""
            INSERT INTO document_segments_fts(
                document_segments_fts
            )
            VALUES ('rebuild');
        """)

        # 6. Count indexed segments
        result = connection.execute(
            text("SELECT COUNT(*) FROM document_segments_fts")
        )

        return result.scalar()
