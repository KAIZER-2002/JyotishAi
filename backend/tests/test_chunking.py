"""
Unit tests for the Chunking subsystem.

Covers:
- FixedSizeChunker (chunk size, overlap, paragraph preservation, splitting long paragraphs, small chunk merging)
- HeadingAwareChunker (Markdown/Setext headings, falling back to FixedSizeChunker, section headings in metadata)
- ChunkingService (validation, strategy switching, empty document handling)
- Edge cases (large docs, Unicode characters, metadata propagation)
"""

import pytest
from dataclasses import FrozenInstanceError
from app.domain.rag import KnowledgeDocument, KnowledgeChunk
from app.services.chunking import (
    ChunkingConfig,
    ChunkingService,
    FixedSizeChunker,
    HeadingAwareChunker,
    ChunkingError,
)

# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

def make_doc(content: str, doc_id: str = "doc-123", metadata: dict = None) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=doc_id,
        content=content,
        source="test_source.md",
        metadata=metadata or {"doc_meta": "xyz"}
    )

# ---------------------------------------------------------------------------
# Config Tests
# ---------------------------------------------------------------------------

def test_chunking_config_validation():
    # Valid configs
    config = ChunkingConfig(chunk_size=100, chunk_overlap=10)
    assert config.chunk_size == 100
    assert config.chunk_overlap == 10
    assert config.effective_min_chunk_size == 25  # default is chunk_size // 4

    # Invalid chunk_size
    with pytest.raises(ValueError):
        ChunkingConfig(chunk_size=0)

    # Invalid overlap
    with pytest.raises(ValueError):
        ChunkingConfig(chunk_size=100, chunk_overlap=100)
    with pytest.raises(ValueError):
        ChunkingConfig(chunk_size=100, chunk_overlap=-5)


# ---------------------------------------------------------------------------
# FixedSizeChunker Tests
# ---------------------------------------------------------------------------

def test_fixed_size_chunker_basic():
    chunker = FixedSizeChunker()
    doc = make_doc("Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.")
    config = ChunkingConfig(chunk_size=15, chunk_overlap=0)

    chunks = chunker.chunk(doc, config)
    # Check that it splits on paragraph boundaries if they fit
    assert len(chunks) == 3
    assert chunks[0].content == "Paragraph 1."
    assert chunks[1].content == "Paragraph 2."
    assert chunks[2].content == "Paragraph 3."
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    assert chunks[2].chunk_index == 2

    # Check offsets
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len("Paragraph 1.")


def test_fixed_size_chunker_overlap():
    chunker = FixedSizeChunker()
    # Content has words. We want to check overlap behavior when paragraphs are split or fit.
    # To test overlap, let's create a single long paragraph that gets split, or multiple paragraphs.
    # If we have a single paragraph of 60 chars, and chunk_size=40, overlap=15
    doc = make_doc("This is a single very long paragraph that will definitely be split.")
    config = ChunkingConfig(chunk_size=40, chunk_overlap=15)

    chunks = chunker.chunk(doc, config)
    assert len(chunks) > 1

    # Verify overlap characters are carried forward.
    # The first chunk content: "This is a single very long paragraph that" (41 chars, wait, it splits on space)
    # Let's inspect the actual contents.
    for i, c in enumerate(chunks):
        assert len(c.content) <= config.chunk_size + 15  # word boundary might add slightly
        if i > 0:
            # There should be overlap text from the previous chunk
            prev_content = chunks[i-1].content
            # The start of the current chunk should match the end of the previous chunk
            overlap_area = prev_content[-config.chunk_overlap:].strip()
            assert overlap_area in c.content


def test_fixed_size_chunker_split_long_paragraph():
    chunker = FixedSizeChunker()
    # A single paragraph with no double-newline, longer than chunk_size
    content = "A" * 100 + " " + "B" * 100
    doc = make_doc(content)
    config = ChunkingConfig(chunk_size=110, chunk_overlap=0)

    chunks = chunker.chunk(doc, config)
    assert len(chunks) == 2
    assert "A" in chunks[0].content
    assert "B" in chunks[1].content
    assert chunks[0].start_char == 0
    assert chunks[1].start_char > 100


def test_fixed_size_chunker_merge_small_trailing():
    chunker = FixedSizeChunker()
    # Paragraph 1 is 40 chars. Paragraph 2 is 5 chars.
    # chunk_size = 50, min_chunk_size = 15.
    # If they are split, paragraph 2 would be 5 chars, which is less than min_chunk_size.
    # It should be merged into the previous chunk.
    doc = make_doc("This is paragraph one which is quite long.\n\nTiny.")
    config = ChunkingConfig(chunk_size=50, chunk_overlap=0, min_chunk_size=15)

    chunks = chunker.chunk(doc, config)
    assert len(chunks) == 1
    assert "Tiny." in chunks[0].content


# ---------------------------------------------------------------------------
# HeadingAwareChunker Tests
# ---------------------------------------------------------------------------

def test_heading_aware_chunker_markdown_atx():
    chunker = HeadingAwareChunker()
    content = (
        "# Introduction\n"
        "This is the intro text.\n"
        "## Section 1\n"
        "This is section 1 text.\n"
        "### Subsection 1.1\n"
        "This is subsection text."
    )
    doc = make_doc(content)
    config = ChunkingConfig(chunk_size=100, chunk_overlap=0)

    chunks = chunker.chunk(doc, config)
    # Should have split on headings
    assert len(chunks) == 3
    assert chunks[0].metadata.get("section_heading") == "Introduction"
    assert chunks[1].metadata.get("section_heading") == "Section 1"
    assert chunks[2].metadata.get("section_heading") == "Subsection 1.1"

    assert "This is the intro text." in chunks[0].content
    assert "Section 1" in chunks[1].content


def test_heading_aware_chunker_setext():
    chunker = HeadingAwareChunker()
    content = (
        "Introduction Heading\n"
        "===\n"
        "Intro text here.\n"
        "Section Heading\n"
        "---\n"
        "Section text here."
    )
    doc = make_doc(content)
    config = ChunkingConfig(chunk_size=150, chunk_overlap=0)

    chunks = chunker.chunk(doc, config)
    assert len(chunks) == 2
    assert chunks[0].metadata.get("section_heading") == "Introduction Heading"
    assert chunks[1].metadata.get("section_heading") == "Section Heading"


def test_heading_aware_chunker_oversized_section():
    chunker = HeadingAwareChunker()
    # Heading followed by text that is much larger than chunk_size.
    # It should split that section using the FixedSizeChunker strategy,
    # but still propagate the section heading metadata to all sub-chunks.
    heading_text = "# Big Section\n"
    body_text = ("This is a paragraph that will be repeated to make it huge.\n\n") * 10
    content = heading_text + body_text
    doc = make_doc(content)
    config = ChunkingConfig(chunk_size=100, chunk_overlap=10)

    chunks = chunker.chunk(doc, config)
    assert len(chunks) > 1
    for c in chunks:
        assert c.metadata.get("section_heading") == "Big Section"


def test_heading_aware_chunker_no_headings_fallback():
    chunker = HeadingAwareChunker()
    # Document with no headings should fall back to FixedSizeChunker
    content = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
    doc = make_doc(content)
    config = ChunkingConfig(chunk_size=15, chunk_overlap=0)

    chunks = chunker.chunk(doc, config)
    assert len(chunks) == 3
    assert chunks[0].content == "Paragraph 1."


# ---------------------------------------------------------------------------
# ChunkingService Tests
# ---------------------------------------------------------------------------

def test_chunking_service_basic():
    service = ChunkingService(FixedSizeChunker())
    doc = make_doc("Hello world.\n\nThis is a test.")
    config = ChunkingConfig(chunk_size=15)

    chunks = service.chunk_document(doc, config)
    assert len(chunks) == 2
    assert chunks[0].document_id == doc.id
    assert chunks[0].chunk_index == 0


def test_chunking_service_validation_failure():
    service = ChunkingService(FixedSizeChunker())
    doc = make_doc("Hello world.")
    config = ChunkingConfig(chunk_size=50)

    # Let's mock the chunker to return an invalid chunk index or wrong doc_id
    class BadChunker(FixedSizeChunker):
        def chunk(self, d, c):
            return [
                KnowledgeChunk(
                    id="123",
                    document_id="wrong_doc_id",
                    content="Hello",
                    chunk_index=0
                )
            ]

    service.set_strategy(BadChunker())
    with pytest.raises(ChunkingError, match="wrong_doc_id"):
        service.chunk_document(doc, config)


@pytest.mark.asyncio
async def test_chunking_service_async():
    service = ChunkingService(FixedSizeChunker())
    doc = make_doc("Hello world.\n\nThis is a test.")
    config = ChunkingConfig(chunk_size=15)

    chunks = await service.achunk_document(doc, config)
    assert len(chunks) == 2


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

def test_chunking_empty_document():
    service = ChunkingService()
    doc = make_doc("")
    config = ChunkingConfig(chunk_size=50)
    assert service.chunk_document(doc, config) == []

    # Whitespace only
    doc_ws = make_doc("   \n\n   ")
    assert service.chunk_document(doc_ws, config) == []


def test_chunking_unicode_content():
    service = ChunkingService()
    # Hindi/Sanskrit content with distinct characters
    doc = make_doc("नमस्ते दुनिया।\n\nयह एक परीक्षण है।")
    config = ChunkingConfig(chunk_size=20)

    chunks = service.chunk_document(doc, config)
    assert len(chunks) == 2
    assert "नमस्ते" in chunks[0].content
    assert "परीक्षण" in chunks[1].content


def test_chunking_metadata_propagation():
    service = ChunkingService()
    doc = make_doc("Content...", metadata={"author": "Sage", "language": "sanskrit"})
    config = ChunkingConfig(chunk_size=50, inherit_document_metadata=True)

    chunks = service.chunk_document(doc, config)
    assert len(chunks) == 1
    assert chunks[0].metadata["author"] == "Sage"
    assert chunks[0].metadata["language"] == "sanskrit"

    # Disable inheritance
    config_no_inherit = ChunkingConfig(chunk_size=50, inherit_document_metadata=False)
    chunks_no_inherit = service.chunk_document(doc, config_no_inherit)
    assert len(chunks_no_inherit) == 1
    assert "author" not in chunks_no_inherit[0].metadata


def test_chunking_large_document():
    service = ChunkingService()
    # 5000 characters
    content = "Word " * 1000
    doc = make_doc(content)
    config = ChunkingConfig(chunk_size=500, chunk_overlap=50)

    chunks = service.chunk_document(doc, config)
    assert len(chunks) > 0
    # Confirm ordering and non-emptiness
    last_end = -1
    for chunk in chunks:
        assert chunk.content.strip()
        assert chunk.start_char >= last_end - config.chunk_overlap
        last_end = chunk.end_char
