"""
Document Ingestion subsystem.

Converts uploaded files into KnowledgeDocument domain objects that are
ready to be chunked and stored in a VectorStore.

Public surface
--------------
Exceptions:
    IngestionError          — base for all ingestion failures
    UnsupportedFileTypeError — file type has no registered parser
    EmptyDocumentError       — parser produced no usable text

Enumerations:
    DocumentMediaType        — canonical supported MIME types

Value object:
    ParsedDocument           — intermediate result before ID assignment

Interfaces:
    DocumentParser (ABC)     — one implementation per file type

Parsers (concrete):
    PDFParser                — PDF via pypdf
    MarkdownParser           — Markdown via stdlib regex
    TextParser               — Plain text, UTF-8

Services:
    DocumentNormalizer       — cleans and normalises raw extracted text
    DocumentIngestionService — orchestrates selection, parsing, normalisation
"""

from __future__ import annotations

import hashlib
import io
import re
import unicodedata
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.domain.rag import KnowledgeDocument, Metadata


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class IngestionError(Exception):
    """Base exception for all document ingestion failures."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when no parser is registered for the given file type."""


class EmptyDocumentError(IngestionError):
    """Raised when a file is parsed but yields no usable text content."""


# ---------------------------------------------------------------------------
# Enumeration — supported media types
# ---------------------------------------------------------------------------


class DocumentMediaType:
    """
    Canonical MIME type strings for file types supported by the ingestion
    pipeline.

    Kept as simple string constants (rather than an Enum) so that callers can
    extend the set without subclassing.
    """

    PDF = "application/pdf"
    MARKDOWN = "text/markdown"
    PLAIN_TEXT = "text/plain"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # File-extension → media-type mapping used by the service layer
    _EXT_MAP: dict[str, str] = {
        ".pdf": PDF,
        ".md": MARKDOWN,
        ".markdown": MARKDOWN,
        ".txt": PLAIN_TEXT,
        ".text": PLAIN_TEXT,
        ".docx": DOCX,
    }

    @classmethod
    def from_extension(cls, extension: str) -> str | None:
        """
        Return the canonical media type for a file extension (leading dot
        required, case-insensitive), or *None* if unknown.
        """
        return cls._EXT_MAP.get(extension.lower())

    @classmethod
    def from_filename(cls, filename: str) -> str | None:
        """Derive the media type from a filename or path string."""
        return cls.from_extension(Path(filename).suffix)


# ---------------------------------------------------------------------------
# Intermediate value object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedDocument:
    """
    Intermediate result produced by a DocumentParser before a stable ID is
    assigned by the DocumentIngestionService.

    Attributes
    ----------
    title:
        Best-effort document title extracted from the content (e.g. the
        first heading in a Markdown file or the PDF metadata title).
        Empty string when no title could be determined.
    content:
        Full extracted text, post-normalisation.
    source:
        Human-readable origin of the file (e.g. the original filename).
    metadata:
        Parser-specific key/value pairs (page count, author, etc.).
    media_type:
        The canonical media type string (one of DocumentMediaType.*).
    """

    title: str
    content: str
    source: str
    metadata: Metadata
    media_type: str


# ---------------------------------------------------------------------------
# DocumentParser (ABC)
# ---------------------------------------------------------------------------


class DocumentParser(ABC):
    """
    Abstract base class for file-type-specific document parsers.

    Each concrete parser is responsible for a single file type.  It receives
    raw bytes and returns a ParsedDocument.  All IO, decoding, and
    format-specific extraction logic lives here; normalisation is handled
    separately by DocumentNormalizer.
    """

    @property
    @abstractmethod
    def supported_media_type(self) -> str:
        """The MIME type string this parser handles (e.g. ``'application/pdf'``)."""

    @abstractmethod
    def parse(self, data: bytes, filename: str) -> ParsedDocument:
        """
        Parse raw file bytes into a ParsedDocument.

        Parameters
        ----------
        data:
            Raw file bytes.  Must not be empty.
        filename:
            Original filename used for source provenance and metadata.

        Returns
        -------
        ParsedDocument
            Extracted text, title, and metadata.

        Raises
        ------
        IngestionError
            If the data cannot be parsed.
        EmptyDocumentError
            If no usable text is found.
        """


# ---------------------------------------------------------------------------
# DocumentNormalizer
# ---------------------------------------------------------------------------


class DocumentNormalizer:
    """
    Cleans and normalises raw text extracted by a DocumentParser.

    Operations (applied in order)
    --------------------------------
    1. Unicode NFKC normalisation (unifies visually similar characters).
    2. Strip null bytes and control characters (except ``\\n``, ``\\t``).
    3. Replace Windows line endings (``\\r\\n``) with ``\\n``.
    4. Collapse runs of more than two consecutive blank lines to two.
    5. Strip leading/trailing whitespace from each line.
    6. Strip overall leading/trailing whitespace from the document.
    """

    # Characters that are safe to keep alongside printable text
    _SAFE_CONTROLS = {"\n", "\t"}

    def normalize(self, text: str) -> str:
        """Return a clean, normalised version of *text*."""
        # 1. Unicode normalisation
        text = unicodedata.normalize("NFKC", text)

        # 2. Remove unsafe control characters
        text = "".join(
            ch for ch in text
            if ch in self._SAFE_CONTROLS or not unicodedata.category(ch).startswith("C")
        )

        # 3. Unify line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 4. Collapse excessive blank lines (> 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 5. Strip trailing whitespace from each line
        text = "\n".join(line.rstrip() for line in text.split("\n"))

        # 6. Overall strip
        return text.strip()


# ---------------------------------------------------------------------------
# Concrete parsers
# ---------------------------------------------------------------------------


class PDFParser(DocumentParser):
    """
    Parses PDF files using ``pypdf``.

    Extracts:
    - Text content from all pages.
    - PDF metadata (title, author, creator, producer, creation date).
    - Page count.

    The text is assembled page-by-page with a double newline separator so
    that DocumentNormalizer can later collapse whitespace uniformly.
    """

    @property
    def supported_media_type(self) -> str:
        return DocumentMediaType.PDF

    def parse(self, data: bytes, filename: str) -> ParsedDocument:
        if not data:
            raise EmptyDocumentError(f"PDF file '{filename}' is empty.")

        try:
            import pypdf  # local import so the rest of the module is testable without pypdf
        except ImportError as exc:
            raise IngestionError(
                "pypdf is not installed. Install it with: pip install pypdf"
            ) from exc

        try:
            reader = pypdf.PdfReader(io.BytesIO(data))
        except Exception as exc:
            raise IngestionError(f"Failed to parse PDF '{filename}': {exc}") from exc

        # Extract text from all pages
        pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)

        raw_text = "\n\n".join(pages)

        if not raw_text.strip():
            raise EmptyDocumentError(
                f"PDF '{filename}' contains no extractable text (may be image-only)."
            )

        # Extract PDF metadata
        pdf_meta = reader.metadata or {}
        title: str = str(pdf_meta.get("/Title", "") or "").strip()
        author: str = str(pdf_meta.get("/Author", "") or "").strip()
        creator: str = str(pdf_meta.get("/Creator", "") or "").strip()
        producer: str = str(pdf_meta.get("/Producer", "") or "").strip()
        creation_date: str = str(pdf_meta.get("/CreationDate", "") or "").strip()

        if not title:
            # Fall back to the filename stem
            title = Path(filename).stem

        metadata: Metadata = {
            "page_count": len(reader.pages),
            "author": author,
            "creator": creator,
            "producer": producer,
            "creation_date": creation_date,
        }

        return ParsedDocument(
            title=title,
            content=raw_text,
            source=filename,
            metadata=metadata,
            media_type=DocumentMediaType.PDF,
        )


class MarkdownParser(DocumentParser):
    """
    Parses Markdown files using stdlib regex (no external Markdown library
    required).

    Extracts:
    - Title from the first ATX heading (``# Heading``) or front matter
      ``title:`` field.
    - Full raw Markdown content (preserved for RAG use — embedding models
      handle Markdown syntax well).
    - Front matter metadata (YAML-style ``key: value`` pairs between
      ``---`` fences).

    The raw Markdown is preserved rather than stripped so that chunking
    strategies can later use heading structure for semantic splitting.
    """

    # Matches a YAML front matter block at the start of the file
    _FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    # Matches a YAML key: value pair (simple scalars only)
    _KV_RE = re.compile(r"^([A-Za-z_][\w]*)\s*:\s*(.+)$")
    # Matches ATX headings: # H1, ## H2, …
    _HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)

    @property
    def supported_media_type(self) -> str:
        return DocumentMediaType.MARKDOWN

    def parse(self, data: bytes, filename: str) -> ParsedDocument:
        if not data:
            raise EmptyDocumentError(f"Markdown file '{filename}' is empty.")

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise IngestionError(
                f"Markdown file '{filename}' is not valid UTF-8: {exc}"
            ) from exc

        if not text.strip():
            raise EmptyDocumentError(f"Markdown file '{filename}' contains no content.")

        # --- Parse optional YAML front matter ---
        frontmatter_meta: Metadata = {}
        fm_match = self._FRONTMATTER_RE.match(text)
        if fm_match:
            for line in fm_match.group(1).splitlines():
                kv = self._KV_RE.match(line.strip())
                if kv:
                    frontmatter_meta[kv.group(1)] = kv.group(2).strip()

        # Strip front matter from the body for heading extraction
        body = text[fm_match.end():] if fm_match else text

        # --- Extract title ---
        # 1. From front matter
        title: str = str(frontmatter_meta.pop("title", "")).strip()

        # 2. From first H1 heading
        if not title:
            heading_match = self._HEADING_RE.search(body)
            if heading_match:
                title = heading_match.group(1).strip()

        # 3. Fall back to filename stem
        if not title:
            title = Path(filename).stem

        # Count headings for metadata
        headings = self._HEADING_RE.findall(body)

        metadata: Metadata = {
            "heading_count": len(headings),
            **frontmatter_meta,
        }

        return ParsedDocument(
            title=title,
            content=text,  # preserve full Markdown including front matter
            source=filename,
            metadata=metadata,
            media_type=DocumentMediaType.MARKDOWN,
        )


class TextParser(DocumentParser):
    """
    Parses plain-text (``.txt``) files.

    Attempts UTF-8 decoding first; falls back to Latin-1 (which never fails
    for byte data) so that legacy files are never silently dropped.

    Extracts:
    - Title from the first non-empty line of the file.
    - Full text content.
    - Character count metadata.
    """

    @property
    def supported_media_type(self) -> str:
        return DocumentMediaType.PLAIN_TEXT

    def parse(self, data: bytes, filename: str) -> ParsedDocument:
        if not data:
            raise EmptyDocumentError(f"Text file '{filename}' is empty.")

        # Attempt UTF-8; fall back to Latin-1
        try:
            text = data.decode("utf-8")
            encoding_used = "utf-8"
        except UnicodeDecodeError:
            text = data.decode("latin-1")
            encoding_used = "latin-1"

        if not text.strip():
            raise EmptyDocumentError(f"Text file '{filename}' contains no content.")

        # Title = first non-empty line, truncated to 120 chars
        title = ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                title = stripped[:120]
                break
        if not title:
            title = Path(filename).stem

        metadata: Metadata = {
            "char_count": len(text),
            "line_count": text.count("\n") + 1,
            "encoding": encoding_used,
        }

        return ParsedDocument(
            title=title,
            content=text,
            source=filename,
            metadata=metadata,
            media_type=DocumentMediaType.PLAIN_TEXT,
        )


class DOCXParser(DocumentParser):
    """
    Parses DOCX files using standard library xml/zipfile.

    Extracts:
    - Text content from paragraphs.
    - Title from the filename.
    - Character count metadata.
    """

    @property
    def supported_media_type(self) -> str:
        return DocumentMediaType.DOCX

    def parse(self, data: bytes, filename: str) -> ParsedDocument:
        if not data:
            raise EmptyDocumentError(f"DOCX file '{filename}' is empty.")

        try:
            import zipfile
            import xml.etree.ElementTree as ET

            with zipfile.ZipFile(io.BytesIO(data)) as docx:
                xml_content = docx.read('word/document.xml')
                root = ET.fromstring(xml_content)

                # Find all text elements under paragraphs
                paragraphs = []
                for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    texts = [node.text for node in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                    if texts:
                        paragraphs.append("".join(texts))

                raw_text = "\n\n".join(paragraphs)
        except Exception as exc:
            raise IngestionError(f"Failed to parse DOCX '{filename}': {exc}") from exc

        if not raw_text.strip():
            raise EmptyDocumentError(f"DOCX '{filename}' contains no extractable text.")

        title = Path(filename).stem
        metadata: Metadata = {
            "char_count": len(raw_text),
            "paragraph_count": len(paragraphs),
        }

        return ParsedDocument(
            title=title,
            content=raw_text,
            source=filename,
            metadata=metadata,
            media_type=DocumentMediaType.DOCX,
        )


# ---------------------------------------------------------------------------
# DocumentIngestionService
# ---------------------------------------------------------------------------


class DocumentIngestionService:
    """
    Orchestrates parser selection, text normalisation, and KnowledgeDocument
    creation from raw uploaded file bytes.

    Responsibilities
    ----------------
    * Select the correct DocumentParser based on the file's extension or an
      explicit media_type override.
    * Delegate parsing to the selected parser.
    * Pass the raw extracted text through DocumentNormalizer.
    * Assign a stable, content-addressed ID to the document.
    * Return a KnowledgeDocument ready for downstream chunking.

    The service is stateless — it holds no open connections or file handles —
    and is safe to use concurrently.

    Parameters
    ----------
    normalizer:
        DocumentNormalizer instance used to clean extracted text.
        Defaults to a freshly constructed DocumentNormalizer.
    extra_parsers:
        Additional DocumentParser instances to register alongside the
        built-in PDF, Markdown, and Text parsers.  If an extra parser shares
        a media type with a built-in one it takes precedence.
    """

    def __init__(
        self,
        normalizer: DocumentNormalizer | None = None,
        extra_parsers: list[DocumentParser] | None = None,
    ) -> None:
        self._normalizer = normalizer or DocumentNormalizer()

        # Register built-in parsers
        built_ins: list[DocumentParser] = [PDFParser(), MarkdownParser(), TextParser(), DOCXParser()]
        self._parsers: dict[str, DocumentParser] = {
            p.supported_media_type: p for p in built_ins
        }

        # Extra parsers override built-ins if they share a media type
        for parser in (extra_parsers or []):
            self._parsers[parser.supported_media_type] = parser

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self,
        data: bytes,
        filename: str,
        media_type: str | None = None,
        extra_metadata: Metadata | None = None,
    ) -> KnowledgeDocument:
        """
        Parse, normalise, and wrap raw file bytes as a KnowledgeDocument.

        Parameters
        ----------
        data:
            Raw bytes of the uploaded file.
        filename:
            Original filename (used for provenance and MIME detection when
            *media_type* is not supplied).
        media_type:
            Explicit MIME type override.  When None, the type is inferred
            from the file extension.
        extra_metadata:
            Caller-supplied key/value pairs merged into the document metadata
            (e.g. ``{"uploaded_by": "user-123"}``).

        Returns
        -------
        KnowledgeDocument
            Fully formed document with a stable, content-addressed id.

        Raises
        ------
        UnsupportedFileTypeError
            If no parser is registered for the detected media type.
        EmptyDocumentError
            If the parsed content is empty after normalisation.
        IngestionError
            For any other parsing failure.
        """
        resolved_type = media_type or DocumentMediaType.from_filename(filename)
        if resolved_type is None:
            raise UnsupportedFileTypeError(
                f"Cannot determine file type for '{filename}'. "
                "Supply an explicit media_type or use a recognised extension "
                "(.pdf, .md, .markdown, .txt, .text)."
            )

        parser = self._parsers.get(resolved_type)
        if parser is None:
            raise UnsupportedFileTypeError(
                f"No parser registered for media type '{resolved_type}'."
            )

        parsed = parser.parse(data, filename)

        # Normalise the extracted content
        clean_content = self._normalizer.normalize(parsed.content)
        if not clean_content:
            raise EmptyDocumentError(
                f"Document '{filename}' contains no usable text after normalisation."
            )

        # Stable, content-addressed document id (SHA-256 of the raw bytes)
        doc_id = self._make_id(data, filename)

        # Merge metadata: parser metadata first, then caller overrides
        merged_meta: Metadata = {
            **parsed.metadata,
            "title": parsed.title,
            "media_type": parsed.media_type,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            **(extra_metadata or {}),
        }

        return KnowledgeDocument(
            id=doc_id,
            content=clean_content,
            source=parsed.source,
            metadata=merged_meta,
        )

    async def aingest(
        self,
        data: bytes,
        filename: str,
        media_type: str | None = None,
        extra_metadata: Metadata | None = None,
    ) -> KnowledgeDocument:
        """
        Asynchronous variant of :meth:`ingest`.

        Parsing and normalisation are CPU-bound operations; this method
        wraps the synchronous implementation so callers in async contexts
        (e.g. FastAPI route handlers) can ``await`` it without blocking
        the event loop via an executor if needed.

        In this implementation the work runs on the calling thread.
        A production implementation may off-load to a thread-pool via
        ``asyncio.get_event_loop().run_in_executor()``.
        """
        return self.ingest(
            data=data,
            filename=filename,
            media_type=media_type,
            extra_metadata=extra_metadata,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_id(data: bytes, filename: str) -> str:
        """
        Create a stable, content-addressed document ID.

        The ID is the first 16 hex chars of SHA-256(data + filename) which
        provides a good balance between uniqueness and readability.
        """
        digest = hashlib.sha256(data + filename.encode()).hexdigest()
        return digest[:32]

    def supported_extensions(self) -> list[str]:
        """
        Return the file extensions the service can currently handle.

        Derived from the registered parsers' media types.
        """
        ext_map = DocumentMediaType._EXT_MAP
        supported: list[str] = [
            ext for ext, mt in ext_map.items() if mt in self._parsers
        ]
        return sorted(supported)

    def register_parser(self, parser: DocumentParser) -> None:
        """
        Register an additional (or replacement) parser at runtime.

        Parameters
        ----------
        parser:
            The parser to register.  Its ``supported_media_type`` is used as
            the key; an existing entry for the same type is replaced.
        """
        self._parsers[parser.supported_media_type] = parser
