"""Semantic chunker: split extracted text into coherent paragraph/topic-based chunks."""

from dataclasses import dataclass


@dataclass
class Chunk:
    """A coherent text chunk from a document."""

    index: int
    text: str
    char_start: int
    char_end: int


# Target chunk sizes
MIN_CHUNK_CHARS = 200
MAX_CHUNK_CHARS = 1500
IDEAL_CHUNK_CHARS = 800


def chunk_text(text: str) -> list[Chunk]:
    """
    Split text into coherent chunks based on paragraph/topic boundaries.

    Strategy:
    1. Split on double-newlines (paragraph breaks) first
    2. Merge small paragraphs into chunks until they reach ideal size
    3. Split overly long paragraphs at sentence boundaries

    Args:
        text: Plain text extracted from a document

    Returns:
        List of Chunk objects with text and position info
    """
    if not text.strip():
        return []

    # Step 1: Split into paragraphs
    paragraphs = _split_paragraphs(text)

    if not paragraphs:
        return []

    # Step 2: Merge small paragraphs, split large ones
    chunks: list[Chunk] = []
    current_text = ""
    current_start = 0
    char_offset = 0

    for para in paragraphs:
        para_start = text.find(para, char_offset)
        if para_start == -1:
            para_start = char_offset

        # If this paragraph alone exceeds max, split it at sentence boundaries
        if len(para) > MAX_CHUNK_CHARS:
            # Flush current buffer first
            if current_text.strip():
                chunks.append(
                    Chunk(
                        index=len(chunks),
                        text=current_text.strip(),
                        char_start=current_start,
                        char_end=current_start + len(current_text.strip()),
                    )
                )
                current_text = ""

            # Split the long paragraph into sentences
            for sentence_chunk in _split_long_text(para):
                chunks.append(
                    Chunk(
                        index=len(chunks),
                        text=sentence_chunk.strip(),
                        char_start=para_start,
                        char_end=para_start + len(sentence_chunk.strip()),
                    )
                )
            char_offset = para_start + len(para)
            current_start = char_offset
            continue

        # Would adding this paragraph exceed ideal size?
        combined = (current_text + "\n\n" + para).strip() if current_text else para
        if len(combined) > IDEAL_CHUNK_CHARS and current_text.strip():
            # Flush current chunk
            chunks.append(
                Chunk(
                    index=len(chunks),
                    text=current_text.strip(),
                    char_start=current_start,
                    char_end=current_start + len(current_text.strip()),
                )
            )
            current_text = para
            current_start = para_start
        else:
            if not current_text:
                current_start = para_start
            current_text = combined

        char_offset = para_start + len(para)

    # Flush remaining
    if current_text.strip():
        chunks.append(
            Chunk(
                index=len(chunks),
                text=current_text.strip(),
                char_start=current_start,
                char_end=current_start + len(current_text.strip()),
            )
        )

    return chunks


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on double-newlines."""
    raw = text.split("\n\n")
    return [p.strip() for p in raw if p.strip()]


def _split_long_text(text: str) -> list[str]:
    """Split a long text block into chunks at sentence boundaries."""
    sentences = _split_sentences(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = (current + " " + sentence).strip() if current else sentence
        if len(candidate) > MAX_CHUNK_CHARS and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = candidate

    if current.strip():
        chunks.append(current.strip())

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Simple sentence splitting on period/exclamation/question followed by space."""
    sentences: list[str] = []
    current = ""

    for i, char in enumerate(text):
        current += char
        if char in ".!?" and i + 1 < len(text) and text[i + 1] == " ":
            sentences.append(current.strip())
            current = ""

    if current.strip():
        sentences.append(current.strip())

    return sentences
