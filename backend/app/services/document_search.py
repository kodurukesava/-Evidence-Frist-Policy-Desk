
import re

from sqlalchemy import text
from sqlalchemy.orm import Session


def search_document_segments(
    db: Session,
    workspace_id: int,
    query: str,
    limit: int = 10,
):
    """
    Search document segments using SQLite FTS5.

    Searches only documents belonging to the specified workspace
    and their current document versions.
    """

    # 1. Validate search query
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    # 2. Extract searchable words
    words = re.findall(r"[\w]+", query, flags=re.UNICODE)

    if not words:
        raise ValueError("Search query contains no searchable words.")

    # 3. Build a safe FTS5 query.
    # All terms must match.
    fts_query = " AND ".join(
        f'"{word.replace(chr(34), chr(34) * 2)}"'
        for word in words
    )

    # 4. Validate result limit
    limit = max(1, min(limit, 50))

    # 5. Search current document versions in the workspace
    sql = text("""
        SELECT
            ds.id AS segment_id,
            ds.document_version_id AS version_id,
            dv.document_id AS document_id,
            d.original_filename AS document_name,
            d.workspace_id AS workspace_id,
            ds.segment_index AS segment_index,
            ds.section_title AS section_title,
            ds.content AS content,
            bm25(document_segments_fts) AS relevance_score

        FROM document_segments_fts

        JOIN document_segments AS ds
            ON ds.id = document_segments_fts.rowid

        JOIN document_versions AS dv
            ON dv.id = ds.document_version_id

        JOIN documents AS d
            ON d.id = dv.document_id

        WHERE document_segments_fts MATCH :fts_query
          AND d.workspace_id = :workspace_id
          AND dv.is_current = 1

        ORDER BY bm25(document_segments_fts) ASC

        LIMIT :limit
    """)

    # 6. Execute search
    results = db.execute(
        sql,
        {
            "fts_query": fts_query,
            "workspace_id": workspace_id,
            "limit": limit,
        },
    ).mappings().all()

    return [dict(row) for row in results]
