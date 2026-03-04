"""File parsers — strategy pattern for PDF and plain-text files.

Each parser accepts raw bytes and returns the extracted text string.
"""

import logging

import fitz  # type: ignore[import-untyped]

from app.core.exceptions import ContentProcessingError, UnsupportedFileTypeError

logger = logging.getLogger(__name__)

_SUPPORTED_TYPES = {"pdf", "text"}


def parse_file(file_type: str, data: bytes) -> str:
    """Dispatch to the correct parser based on *file_type*."""
    if file_type not in _SUPPORTED_TYPES:
        raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}")
    if file_type == "pdf":
        return _parse_pdf(data)
    return _parse_text(data)


def _parse_pdf(data: bytes) -> str:
    """Extract all text from a PDF byte stream using PyMuPDF."""
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        pages = [page.get_text() for page in doc]
        return "\n".join(pages)
    except Exception as exc:
        logger.error("PDF parsing failed: %s", exc)
        raise ContentProcessingError("Failed to parse PDF") from exc


def _parse_text(data: bytes) -> str:
    """Decode raw bytes as UTF-8 text."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContentProcessingError("File is not valid UTF-8 text") from exc
