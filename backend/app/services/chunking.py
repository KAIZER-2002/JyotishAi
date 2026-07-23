"""
Chunking subsystem.

Splits KnowledgeDocument objects into KnowledgeChunk sequences ready for
embedding and vector storage.

No network calls, no embeddings, no Qdrant, no FastAPI, no SQLAlchemy.

Public surface
--------------
Exceptions:
    ChunkingError           — base for all chunking failures

Value objects:
    ChunkingConfig          — shared configuration for all strategies

Interfaces:
    ChunkingStrategy (ABC)  — one implementation per splitting approach

Strategies (concrete):
    FixedSizeChunker        — character-count window with configurable overlap
    HeadingAwareChunker     — splits on Markdown/text headings; falls back to
                              FixedSizeChunker for oversized sections

Services:
    ChunkingService         — selects a strategy and drives the pipeline
"""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.domain.rag import KnowledgeChunk, KnowledgeDocument, Metadata


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ChunkingError(Exception):
    """Base exception for all chunking failures."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChunkingConfig:
    """
    Shared, immutable configuration used by all ChunkingStrategy implementations.

    Attributes
    ----------
    chunk_size:
        Target maximum character count per chunk.  The chunker may produce
        slightly larger chunks when it must preserve a complete paragraph or
        heading section.  Must be ≥ 1.
    chunk_overlap:
        Number of characters carried forward from the end of one chunk into
        the beginning of the next.  Provides context continuity for the
        embedding model.  Must be in the range [0, chunk_size).
    min_chunk_size:
        Chunks shorter than this threshold are merged with the previous chunk
        rather than emitted as standalone entries.  Prevents orphan fragments.
        Defaults to ``chunk_size // 4``.
    paragraph_separator:
        The string used to detect paragraph boundaries.  Defaults to a
        double newline (``\"\\n\\n\"``).
    inherit_document_metadata:
        When True, each chunk's metadata is pre-populated with a copy of the
        parent document's metadata.  Callers can always override individual
        keys with ``extra_metadata`` on the chunk.  Defaults to True.
    """

    chunk_size: int
    chunk_overlap: int = 0
    min_chunk_size: int = -1          # -1 → computed as chunk_size // 4
    paragraph_separator: str = "\n\n"
    inherit_document_metadata: bool = True

    def __post_init__(self) -> None:
        if self.chunk_size < 1:
            raise ValueError(f"chunk_size must be ≥ 1, got {self.chunk_size}")
        if not (0 <= self.chunk_overlap < self.chunk_size):
            raise ValueError(
                f"chunk_overlap must be in [0, chunk_size), "
                f"got overlap={self.chunk_overlap}, chunk_size={self.chunk_size}"
            )

    @property
    def effective_min_chunk_size(self) -> int:
        """Resolved minimum chunk size (handles the -1 default sentinel)."""
        return self.min_chunk_size if self.min_chunk_size >= 0 else self.chunk_size // 4


# ---------------------------------------------------------------------------
# ChunkingStrategy (ABC)
# ---------------------------------------------------------------------------


class ChunkingStrategy(ABC):
    """
    Abstract base class for text splitting strategies.

    Concrete implementations receive a KnowledgeDocument and a ChunkingConfig
    and return an ordered list of KnowledgeChunk objects.

    Design constraints
    ------------------
    * Chunkers must not perform any IO, network requests, or embedding calls.
    * Chunk IDs must be stable: the same document content always produces the
      same IDs (content-addressed using SHA-256).
    * Chunks must be ordered by ascending start_char.
    * Metadata must propagate from the parent document when
      ``config.inherit_document_metadata`` is True.
    """

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Short stable identifier for this strategy (e.g. ``'fixed_size'``)."""

    @abstractmethod
    def chunk(
        self,
        document: KnowledgeDocument,
        config: ChunkingConfig,
    ) -> list[KnowledgeChunk]:
        """
        Split *document* into an ordered list of KnowledgeChunk objects.

        Parameters
        ----------
        document:
            The source document to split.
        config:
            Chunking parameters.

        Returns
        -------
        list[KnowledgeChunk]
            Zero or more chunks in ascending start_char order.
            Returns an empty list when the document has no content.

        Raises
        ------
        ChunkingError
            If the document cannot be split for any reason.
        """

    # ------------------------------------------------------------------
    # Shared helpers available to all subclasses
    # ------------------------------------------------------------------

    @staticmethod
    def _make_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
        """
        Create a stable, content-addressed chunk ID.

        The ID is the first 32 hex chars of
        ``SHA-256(document_id + str(chunk_index) + content)``.
        """
        raw = f"{document_id}::{chunk_index}::{content}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @staticmethod
    def _build_metadata(
        document: KnowledgeDocument,
        config: ChunkingConfig,
        extra: Metadata | None = None,
    ) -> Metadata:
        """
        Construct chunk metadata by (optionally) inheriting from the document
        and overlaying strategy-specific and caller-supplied extras.
        """
        base: Metadata = {}
        if config.inherit_document_metadata:
            base.update(document.metadata)
        if extra:
            base.update(extra)
        return base

    @staticmethod
    def _assemble_chunk(
        document: KnowledgeDocument,
        config: ChunkingConfig,
        content: str,
        chunk_index: int,
        start_char: int,
        end_char: int,
        extra_metadata: Metadata | None = None,
    ) -> KnowledgeChunk:
        """Construct a KnowledgeChunk with a stable ID and correct metadata."""
        meta = ChunkingStrategy._build_metadata(document, config, extra_metadata)
        chunk_id = ChunkingStrategy._make_chunk_id(document.id, chunk_index, content)
        return KnowledgeChunk(
            id=chunk_id,
            document_id=document.id,
            content=content,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
            metadata=meta,
        )


# ---------------------------------------------------------------------------
# FixedSizeChunker
# ---------------------------------------------------------------------------


class FixedSizeChunker(ChunkingStrategy):
    """
    Splits a document using a sliding character window.

    Algorithm
    ---------
    1.  Split the document content into paragraphs (on ``config.paragraph_separator``).
    2.  Greedily fill a window up to ``config.chunk_size`` characters by
        appending whole paragraphs.
    3.  When a paragraph would overflow the window:
        a.  Emit the current window as a chunk.
        b.  Carry ``config.chunk_overlap`` characters forward into the next window.
    4.  Paragraphs longer than ``chunk_size`` are force-split at word boundaries
        so that no individual chunk violates the size contract by more than one
        word length.
    5.  Trailing chunks shorter than ``config.effective_min_chunk_size`` are merged
        with the previous chunk (if one exists) rather than emitted standalone.

    Character offsets (``start_char``, ``end_char``) refer to positions in the
    *original document content string* so that callers can reconstruct context.
    """

    @property
    def strategy_name(self) -> str:
        return "fixed_size"

    def chunk(
        self,
        document: KnowledgeDocument,
        config: ChunkingConfig,
    ) -> list[KnowledgeChunk]:
        text = document.content
        if not text.strip():
            return []

        # Split into paragraphs; preserve the separator length for offset tracking
        sep = config.paragraph_separator
        sep_len = len(sep)
        raw_paragraphs = text.split(sep)

        # Build (paragraph_text, start_offset) pairs
        paragraphs: list[tuple[str, int]] = []
        offset = 0
        for para in raw_paragraphs:
            paragraphs.append((para, offset))
            offset += len(para) + sep_len

        # Expand paragraphs longer than chunk_size into word-boundary sub-paragraphs
        expanded: list[tuple[str, int]] = []
        for para_text, para_start in paragraphs:
            if len(para_text) <= config.chunk_size:
                expanded.append((para_text, para_start))
            else:
                expanded.extend(
                    self._split_long_paragraph(para_text, para_start, config.chunk_size)
                )

        # Sliding window assembly
        windows: list[tuple[str, int, int]] = []  # (text, start, end)
        current_parts: list[str] = []
        current_start: int = 0
        current_len: int = 0

        for i, (para_text, para_start) in enumerate(expanded):
            # Would adding this paragraph overflow the window?
            addition = len(para_text)
            if current_parts:
                addition += sep_len  # separator between paragraphs

            if current_len + addition > config.chunk_size and current_parts:
                # Emit current window
                window_text = sep.join(current_parts)
                window_end = current_start + len(window_text)
                windows.append((window_text, current_start, window_end))

                # Build overlap: take characters from the end of the current window
                overlap_text = window_text[-config.chunk_overlap:] if config.chunk_overlap > 0 else ""
                current_parts = [overlap_text] if overlap_text else []
                current_len = len(overlap_text)
                current_start = window_end - len(overlap_text)

            if not current_parts:
                current_start = para_start

            current_parts.append(para_text)
            current_len = len(sep.join(current_parts))

        # Emit the last window
        if current_parts:
            window_text = sep.join(current_parts)
            window_end = current_start + len(window_text)
            windows.append((window_text, current_start, window_end))

        # Apply min_chunk_size: merge tiny trailing chunks into the previous one
        windows = self._merge_small_windows(windows, config, sep)

        # Assemble KnowledgeChunk objects
        chunks: list[KnowledgeChunk] = []
        for idx, (win_text, win_start, win_end) in enumerate(windows):
            stripped = win_text.strip()
            if not stripped:
                continue
            chunk = self._assemble_chunk(
                document=document,
                config=config,
                content=stripped,
                chunk_index=idx,
                start_char=win_start,
                end_char=win_end,
            )
            chunks.append(chunk)

        # Re-index after potential skips
        return [
            KnowledgeChunk(
                id=c.id,
                document_id=c.document_id,
                content=c.content,
                chunk_index=i,
                start_char=c.start_char,
                end_char=c.end_char,
                metadata=c.metadata,
            )
            for i, c in enumerate(chunks)
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_long_paragraph(
        text: str, start_offset: int, chunk_size: int
    ) -> list[tuple[str, int]]:
        """Force-split a paragraph that exceeds chunk_size at word boundaries."""
        result: list[tuple[str, int]] = []
        current_start = 0

        while current_start < len(text):
            end = current_start + chunk_size
            if end >= len(text):
                result.append((text[current_start:], start_offset + current_start))
                break
            # Back up to the last space within the window
            split_at = text.rfind(" ", current_start, end)
            if split_at == -1 or split_at <= current_start:
                split_at = end  # no space found — hard cut
            result.append((text[current_start:split_at], start_offset + current_start))
            current_start = split_at + 1  # skip the space

        return result

    @staticmethod
    def _merge_small_windows(
        windows: list[tuple[str, int, int]],
        config: ChunkingConfig,
        sep: str,
    ) -> list[tuple[str, int, int]]:
        """Merge trailing tiny windows into their predecessor."""
        min_sz = config.effective_min_chunk_size
        if min_sz <= 0 or len(windows) <= 1:
            return windows

        merged: list[tuple[str, int, int]] = []
        for win_text, win_start, win_end in windows:
            if merged and len(win_text.strip()) < min_sz:
                # Merge into previous
                prev_text, prev_start, _ = merged.pop()
                combined = prev_text + sep + win_text
                merged.append((combined, prev_start, win_end))
            else:
                merged.append((win_text, win_start, win_end))
        return merged


# ---------------------------------------------------------------------------
# HeadingAwareChunker
# ---------------------------------------------------------------------------


class HeadingAwareChunker(ChunkingStrategy):
    """
    Splits a document at Markdown/text heading boundaries.

    Algorithm
    ---------
    1.  Scan the document line-by-line for heading markers.
        Recognised patterns:
          * ATX headings: ``# Title``, ``## Title``, … (levels 1–6)
          * Setext headings: underlined with ``===`` or ``---``
    2.  Each heading starts a new section.  The section text includes the
        heading line itself.
    3.  Sections that fit within ``config.chunk_size`` are emitted as single
        chunks.
    4.  Sections larger than ``config.chunk_size`` are sub-divided using
        FixedSizeChunker with the same config, so the overlap and
        min_chunk_size guarantees still apply within each section.
    5.  The heading text is propagated into each chunk's metadata under the
        key ``"section_heading"``.
    6.  Documents with no headings fall through to FixedSizeChunker.

    Character offsets refer to the original document content.
    """

    # Matches ATX headings (# H1 .. ###### H6)
    _ATX_RE = re.compile(r"^(#{1,6})\s+(.+)$")
    # Matches Setext heading underlines (=== or ---)
    _SETEXT_RE = re.compile(r"^[=\-]{3,}\s*$")

    @property
    def strategy_name(self) -> str:
        return "heading_aware"

    def chunk(
        self,
        document: KnowledgeDocument,
        config: ChunkingConfig,
    ) -> list[KnowledgeChunk]:
        text = document.content
        if not text.strip():
            return []

        sections = self._split_into_sections(text)

        if len(sections) <= 1 and not self._has_headings(text):
            # No structure detected — delegate entirely to FixedSizeChunker
            return FixedSizeChunker().chunk(document, config)

        fallback = FixedSizeChunker()
        all_chunks: list[KnowledgeChunk] = []
        global_index = 0

        for heading, section_text, section_start in sections:
            stripped = section_text.strip()
            if not stripped:
                continue

            if len(stripped) <= config.chunk_size:
                # Section fits in one chunk
                extra_meta: Metadata = {}
                if heading:
                    extra_meta["section_heading"] = heading
                chunk = self._assemble_chunk(
                    document=document,
                    config=config,
                    content=stripped,
                    chunk_index=global_index,
                    start_char=section_start,
                    end_char=section_start + len(section_text),
                    extra_metadata=extra_meta,
                )
                all_chunks.append(chunk)
                global_index += 1
            else:
                # Section is too large — sub-chunk with FixedSizeChunker
                # Create a synthetic sub-document for the section
                sub_doc = KnowledgeDocument(
                    id=document.id,
                    content=section_text,
                    source=document.source,
                    metadata=document.metadata,
                )
                sub_chunks = fallback.chunk(sub_doc, config)
                for sub_chunk in sub_chunks:
                    adjusted_start = section_start + sub_chunk.start_char
                    adjusted_end = section_start + sub_chunk.end_char

                    # Build metadata: inherit from sub_chunk, add heading
                    sub_meta = dict(sub_chunk.metadata)
                    if heading:
                        sub_meta["section_heading"] = heading

                    chunk_id = self._make_chunk_id(
                        document.id, global_index, sub_chunk.content
                    )
                    all_chunks.append(
                        KnowledgeChunk(
                            id=chunk_id,
                            document_id=document.id,
                            content=sub_chunk.content,
                            chunk_index=global_index,
                            start_char=adjusted_start,
                            end_char=adjusted_end,
                            metadata=sub_meta,
                        )
                    )
                    global_index += 1

        return all_chunks

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _has_headings(self, text: str) -> bool:
        """Return True if the text contains at least one detectable heading."""
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if self._ATX_RE.match(line):
                return True
            if i > 0 and self._SETEXT_RE.match(line) and lines[i - 1].strip():
                return True
        return False

    def _split_into_sections(
        self, text: str
    ) -> list[tuple[str, str, int]]:
        """
        Return a list of ``(heading, section_text, start_char_in_doc)`` tuples.

        The first section may have an empty heading string if there is content
        before the first heading.
        """
        lines = text.splitlines(keepends=True)
        sections: list[tuple[str, str, int]] = []

        current_heading = ""
        current_lines: list[str] = []
        current_start = 0
        char_pos = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.rstrip("\n").rstrip("\r")

            # Check ATX heading
            atx_match = self._ATX_RE.match(stripped)
            if atx_match:
                # Flush current section
                if current_lines or sections:
                    sections.append(
                        (current_heading, "".join(current_lines), current_start)
                    )
                current_heading = atx_match.group(2).strip()
                current_lines = [line]
                current_start = char_pos
                char_pos += len(line)
                i += 1
                continue

            # Check Setext heading (underline on *next* line)
            if (
                i + 1 < len(lines)
                and stripped.strip()
                and self._SETEXT_RE.match(lines[i + 1].rstrip("\n").rstrip("\r"))
            ):
                # Flush current section
                if current_lines or sections:
                    sections.append(
                        (current_heading, "".join(current_lines), current_start)
                    )
                current_heading = stripped.strip()
                # Include both the heading line and its underline
                current_lines = [line, lines[i + 1]]
                current_start = char_pos
                char_pos += len(line) + len(lines[i + 1])
                i += 2
                continue

            current_lines.append(line)
            char_pos += len(line)
            i += 1

        # Flush the last section
        if current_lines or (not sections):
            sections.append((current_heading, "".join(current_lines), current_start))

        return sections


# ---------------------------------------------------------------------------
# ChunkingService
# ---------------------------------------------------------------------------


class ChunkingService:
    """
    Orchestrates the chunking pipeline.

    Responsibilities
    ----------------
    * Accept a KnowledgeDocument and a ChunkingConfig.
    * Delegate to the configured ChunkingStrategy.
    * Validate the output (non-empty chunks, correct ordering, stable IDs).
    * Optionally merge chunks that are too small.

    The service is stateless and safe for concurrent use.

    Parameters
    ----------
    strategy:
        The ChunkingStrategy to use.  Defaults to FixedSizeChunker.
    """

    def __init__(self, strategy: ChunkingStrategy | None = None) -> None:
        self._strategy = strategy or FixedSizeChunker()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk_document(
        self,
        document: KnowledgeDocument,
        config: ChunkingConfig,
    ) -> list[KnowledgeChunk]:
        """
        Split a KnowledgeDocument into an ordered list of KnowledgeChunk objects.

        Parameters
        ----------
        document:
            The source document to split.
        config:
            Chunking configuration (chunk_size, overlap, etc.).

        Returns
        -------
        list[KnowledgeChunk]
            Ordered chunks.  Empty when the document has no content.

        Raises
        ------
        ChunkingError
            If the strategy raises or produces invalid output.
        """
        if not document.content.strip():
            return []

        try:
            chunks = self._strategy.chunk(document, config)
        except ChunkingError:
            raise
        except Exception as exc:
            raise ChunkingError(
                f"Strategy '{self._strategy.strategy_name}' failed: {exc}"
            ) from exc

        self._validate(chunks, document.id)
        return chunks

    async def achunk_document(
        self,
        document: KnowledgeDocument,
        config: ChunkingConfig,
    ) -> list[KnowledgeChunk]:
        """
        Async variant of :meth:`chunk_document`.

        Chunking is CPU-bound; this method delegates synchronously.
        A production implementation can off-load to a thread pool via
        ``asyncio.get_event_loop().run_in_executor()``.
        """
        return self.chunk_document(document, config)

    @property
    def strategy(self) -> ChunkingStrategy:
        """The active chunking strategy."""
        return self._strategy

    def set_strategy(self, strategy: ChunkingStrategy) -> None:
        """Replace the active strategy at runtime."""
        self._strategy = strategy

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(chunks: list[KnowledgeChunk], document_id: str) -> None:
        """
        Assert basic structural invariants on the chunk list.

        Raises
        ------
        ChunkingError
            If any invariant is violated.
        """
        for i, chunk in enumerate(chunks):
            if chunk.document_id != document_id:
                raise ChunkingError(
                    f"Chunk {i} has document_id='{chunk.document_id}' "
                    f"but expected '{document_id}'"
                )
            if chunk.chunk_index != i:
                raise ChunkingError(
                    f"Chunk {i} has chunk_index={chunk.chunk_index} (expected {i})"
                )
            if not chunk.content.strip():
                raise ChunkingError(f"Chunk {i} has empty content")
