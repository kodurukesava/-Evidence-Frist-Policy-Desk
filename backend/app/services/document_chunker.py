
import re

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 50


def split_long_paragraph(paragraph, chunk_size, chunk_overlap):
    """Split a long paragraph at word boundaries."""

    words = paragraph.split()
    chunks = []
    current_words = []

    for word in words:
        candidate = " ".join(current_words + [word])

        if len(candidate) <= chunk_size:
            current_words.append(word)
        else:
            if current_words:
                previous = " ".join(current_words)
                chunks.append(previous)

                # Preserve overlap using complete words.
                overlap_words = []
                overlap_length = 0

                for previous_word in reversed(current_words):
                    extra = len(previous_word) + (
                        1 if overlap_words else 0
                    )

                    if overlap_length + extra > chunk_overlap:
                        break

                    overlap_words.insert(0, previous_word)
                    overlap_length += extra

                current_words = overlap_words

            # A single word larger than the limit is split safely.
            if not current_words and len(word) > chunk_size:
                chunks.append(word[:chunk_size])
                remaining = word[chunk_size:]
                current_words = [remaining] if remaining else []
            else:
                current_words.append(word)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def split_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:

    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be non-negative and smaller than chunk size."
        )

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        if len(paragraph) > chunk_size:

            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            chunks.extend(
                split_long_paragraph(
                    paragraph, chunk_size, chunk_overlap
                )
            )
            continue

        candidate = (
            current_chunk + "\n\n" + paragraph
            if current_chunk
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    return [chunk for chunk in chunks if chunk.strip()]
