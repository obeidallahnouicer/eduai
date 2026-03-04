"""Text chunker — splits a document into fixed-size overlapping chunks."""

from app.core.config import settings

# Characters per chunk and overlap between consecutive chunks
_CHUNK_SIZE = 1500
_CHUNK_OVERLAP = 200


class TextChunker:
    """Splits a long text into overlapping chunks for AI ingestion."""

    def chunk(self, text: str) -> list[str]:
        """Return a list of fixed-size overlapping text chunks."""
        cleaned = self._clean(text)
        return self._split(cleaned)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean(text: str) -> str:
        """Collapse excessive whitespace."""
        return " ".join(text.split())

    @staticmethod
    def _split(text: str) -> list[str]:
        """Slide a window of _CHUNK_SIZE chars over *text*."""
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + _CHUNK_SIZE
            chunks.append(text[start:end])
            start += _CHUNK_SIZE - _CHUNK_OVERLAP
        return chunks
