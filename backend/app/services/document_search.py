
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

    Ranking priority:
    1. Exact phrase matches.
    2. BM25 relevance score.
    3. Stable segment ID ordering.

    Only active documents and their current versions
    from the requested workspace are searched.
    """

    # 1. Validate query
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    # 2. Extract searchable words
    words = re.findall(r"[\w]+", query, flags=re.UNICODE)

    if not words:
        raise ValueError("Search query contains no searchable words.")

    # 3. Remove duplicate terms while preserving order
    unique_words = list(dict.fromkeys(
        word.casefold() for word in words
    ))

    # 4. Build safe FTS5 queries
    quoted_words = [
        f'"{word.replace(chr(34), chr(34) * 2)}"'
        for word in unique_words
    ]

    # All query terms must match.
    fts_query = " AND ".join(quoted_words)

    # Exact phrase query for ranking priority.
    phrase_query = '"' + " ".join(unique_words) + '"'

    # 5. Validate result limit
    limit = max(1, min(limit, 50))

    # 6. Retrieve and rank evidence
    sql = text("""
        WITH phrase_matches AS (
            SELECT rowid
            FROM document_segments_fts
            WHERE document_segments_fts MATCH :phrase_query
        )

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
          AND d.lifecycle_status = 'active'

        ORDER BY
            CASE
                WHEN ds.id IN (
                    SELECT rowid FROM phrase_matches
                )
                THEN 0
                ELSE 1
            END ASC,
            relevance_score ASC,
            ds.id ASC

        LIMIT :limit
    """)

    # 7. Execute search
    results = db.execute(
        sql,
        {
            "fts_query": fts_query,
            "phrase_query": phrase_query,
            "workspace_id": workspace_id,
            "limit": limit,
        },
    ).mappings().all()

    return [dict(row) for row in results]
