"""Text extraction from uploaded documents (.txt, .docx)."""

import io
import os


def extract_text(content: bytes, filename: str) -> str:
    """
    Extract plain text from a file based on its extension.

    Supported formats:
    - .txt: Direct UTF-8 decode
    - .docx: Paragraph extraction via python-docx

    Args:
        content: Raw file bytes
        filename: Original filename (used for extension detection)

    Returns:
        Extracted plain text

    Raises:
        ValueError: If the file format is unsupported
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".txt":
        return _parse_txt(content)
    elif ext == ".docx":
        return _parse_docx(content)
    else:
        raise ValueError(
            f"Unsupported file format: {ext}. Supported formats: .txt, .docx"
        )


def _parse_txt(content: bytes) -> str:
    """Parse plain text file."""
    return content.decode("utf-8", errors="replace").strip()


def _parse_docx(content: bytes) -> str:
    """Parse .docx file using python-docx."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "python-docx is required for .docx parsing. "
            "Install it with: pip install python-docx"
        )

    doc = Document(io.BytesIO(content))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
