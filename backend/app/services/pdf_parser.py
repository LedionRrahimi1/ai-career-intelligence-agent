"""PDF text extraction utilities."""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_pdf(path: Path | str) -> str:
    """Extract text from a PDF using pypdf."""
    from pypdf import PdfReader

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = PdfReader(str(path))
    chunks: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to extract page %s: %s", i, exc)
            text = ""
        if text.strip():
            chunks.append(text.strip())

    full = "\n\n".join(chunks)
    if not full.strip():
        raise ValueError(
            "Could not extract text from PDF. The file may be scanned/image-only."
        )
    return full
