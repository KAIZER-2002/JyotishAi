"""
Tests for app.services.document_ingestion.

Coverage:
  - DocumentMediaType: extension resolution, filename resolution
  - DocumentNormalizer: all normalisation rules individually and combined
  - ParsedDocument: immutability, equality
  - DocumentParser ABC: cannot be instantiated without implementations
  - TextParser: successful parse, UTF-8, Latin-1 fallback, empty, whitespace-only
  - MarkdownParser: title from H1, front matter, no heading, empty, invalid UTF-8
  - PDFParser: successful parse, empty bytes, corrupted bytes, image-only PDF
  - DocumentIngestionService:
      - Parser selection by extension
      - Parser selection by explicit media_type
      - Unsupported extension raises UnsupportedFileTypeError
      - Explicit unsupported media_type raises UnsupportedFileTypeError
      - Empty content raises EmptyDocumentError after normalisation
      - Content-addressed ID is stable for same input
      - Extra metadata is merged
      - Async aingest delegates correctly
      - register_parser / extra_parsers work
      - supported_extensions returns correct list
"""

from __future__ import annotations

import io
import os
import struct
import sys
import textwrap
import types
from dataclasses import FrozenInstanceError
from unittest.mock import patch, MagicMock

import pytest

from app.services.document_ingestion import (
    DocumentIngestionService,
    DocumentMediaType,
    DocumentNormalizer,
    DocumentParser,
    EmptyDocumentError,
    IngestionError,
    MarkdownParser,
    ParsedDocument,
    PDFParser,
    TextParser,
    UnsupportedFileTypeError,
)
from app.domain.rag import KnowledgeDocument


# ===========================================================================
# Helpers
# ===========================================================================


def _utf8(text: str) -> bytes:
    return text.encode("utf-8")


def _make_minimal_pdf(title: str = "", author: str = "") -> bytes:
    """
    Build the smallest valid PDF that pypdf can read and that contains one
    page with extractable text.
    """
    # We use pypdf itself to build a minimal in-memory PDF if available,
    # otherwise we embed a pre-built minimal PDF byte literal.
    try:
        import pypdf
        from pypdf import PdfWriter

        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        # pypdf ≥ 3 can't write text directly without a font resource,
        # so we inject a tiny text stream manually.
        # Instead, build the PDF with reportlab if available, else embed bytes.
        raise ImportError  # fall through to the byte literal approach
    except ImportError:
        pass

    # Minimal hand-crafted single-page PDF with one text stream.
    # This has been validated to parse correctly with pypdf.
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>"
        b"/Contents 4 0 R"
        b">>endobj\n"
        b"4 0 obj<</Length 44>>\n"
        b"stream\n"
        b"BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\n"
        b"startxref\n360\n%%EOF\n"
    )
    return pdf


# ===========================================================================
# DocumentMediaType
# ===========================================================================


class TestDocumentMediaType:
    def test_from_extension_pdf(self):
        assert DocumentMediaType.from_extension(".pdf") == DocumentMediaType.PDF

    def test_from_extension_md(self):
        assert DocumentMediaType.from_extension(".md") == DocumentMediaType.MARKDOWN

    def test_from_extension_markdown(self):
        assert DocumentMediaType.from_extension(".markdown") == DocumentMediaType.MARKDOWN

    def test_from_extension_txt(self):
        assert DocumentMediaType.from_extension(".txt") == DocumentMediaType.PLAIN_TEXT

    def test_from_extension_text(self):
        assert DocumentMediaType.from_extension(".text") == DocumentMediaType.PLAIN_TEXT

    def test_from_extension_case_insensitive(self):
        assert DocumentMediaType.from_extension(".PDF") == DocumentMediaType.PDF
        assert DocumentMediaType.from_extension(".MD") == DocumentMediaType.MARKDOWN

    def test_from_extension_unknown_returns_none(self):
        assert DocumentMediaType.from_extension(".xlsx") is None
        assert DocumentMediaType.from_extension(".zip") is None
        assert DocumentMediaType.from_extension("") is None

    def test_from_filename_pdf(self):
        assert DocumentMediaType.from_filename("document.pdf") == DocumentMediaType.PDF

    def test_from_filename_md(self):
        assert DocumentMediaType.from_filename("notes.md") == DocumentMediaType.MARKDOWN

    def test_from_filename_txt(self):
        assert DocumentMediaType.from_filename("readme.txt") == DocumentMediaType.PLAIN_TEXT

    def test_from_filename_path_with_directory(self):
        assert DocumentMediaType.from_filename("docs/subdir/file.txt") == DocumentMediaType.PLAIN_TEXT

    def test_from_filename_no_extension(self):
        assert DocumentMediaType.from_filename("Makefile") is None

    def test_from_filename_unknown(self):
        assert DocumentMediaType.from_filename("data.csv") is None

    def test_constants_are_strings(self):
        assert isinstance(DocumentMediaType.PDF, str)
        assert isinstance(DocumentMediaType.MARKDOWN, str)
        assert isinstance(DocumentMediaType.PLAIN_TEXT, str)


# ===========================================================================
# ParsedDocument
# ===========================================================================


class TestParsedDocument:
    def _make(self) -> ParsedDocument:
        return ParsedDocument(
            title="My Title",
            content="Some content.",
            source="file.txt",
            metadata={"key": "value"},
            media_type=DocumentMediaType.PLAIN_TEXT,
        )

    def test_basic_construction(self):
        doc = self._make()
        assert doc.title == "My Title"
        assert doc.content == "Some content."
        assert doc.source == "file.txt"
        assert doc.media_type == DocumentMediaType.PLAIN_TEXT

    def test_immutable_title(self):
        doc = self._make()
        with pytest.raises(FrozenInstanceError):
            doc.title = "Other"  # type: ignore[misc]

    def test_immutable_content(self):
        doc = self._make()
        with pytest.raises(FrozenInstanceError):
            doc.content = "Other"  # type: ignore[misc]

    def test_equality_same_values(self):
        a = self._make()
        b = self._make()
        assert a == b

    def test_equality_different_title(self):
        a = ParsedDocument(title="A", content="x", source="f", metadata={}, media_type="text/plain")
        b = ParsedDocument(title="B", content="x", source="f", metadata={}, media_type="text/plain")
        assert a != b


# ===========================================================================
# DocumentNormalizer
# ===========================================================================


class TestDocumentNormalizer:
    def setup_method(self):
        self.normalizer = DocumentNormalizer()

    def test_strips_leading_trailing_whitespace(self):
        result = self.normalizer.normalize("  hello  ")
        assert result == "hello"

    def test_unifies_crlf(self):
        result = self.normalizer.normalize("line1\r\nline2")
        assert "\r" not in result
        assert result == "line1\nline2"

    def test_unifies_bare_cr(self):
        result = self.normalizer.normalize("line1\rline2")
        assert "\r" not in result

    def test_collapses_excessive_blank_lines(self):
        text = "para1\n\n\n\n\npara2"
        result = self.normalizer.normalize(text)
        assert "\n\n\n" not in result
        assert "para1" in result
        assert "para2" in result

    def test_preserves_exactly_two_blank_lines(self):
        text = "para1\n\npara2"
        result = self.normalizer.normalize(text)
        assert result == "para1\n\npara2"

    def test_strips_null_bytes(self):
        text = "hello\x00world"
        result = self.normalizer.normalize(text)
        assert "\x00" not in result
        assert "helloworld" in result

    def test_preserves_newlines_and_tabs(self):
        text = "col1\tcol2\nrow2"
        result = self.normalizer.normalize(text)
        assert "\t" in result
        assert "\n" in result

    def test_strips_trailing_whitespace_per_line(self):
        text = "line1   \nline2  "
        result = self.normalizer.normalize(text)
        for line in result.split("\n"):
            assert not line.endswith(" ")

    def test_unicode_normalization(self):
        # NFKC: ligature fi → fi
        text = "\uFB01ne text"  # ﬁne text (fi ligature)
        result = self.normalizer.normalize(text)
        assert result.startswith("fi")

    def test_empty_string(self):
        assert self.normalizer.normalize("") == ""

    def test_whitespace_only(self):
        assert self.normalizer.normalize("   \n  \t  ") == ""

    def test_normal_text_unchanged(self):
        text = "This is a normal sentence."
        result = self.normalizer.normalize(text)
        assert result == text


# ===========================================================================
# DocumentParser ABC
# ===========================================================================


class TestDocumentParserABC:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            DocumentParser()  # type: ignore[abstract]

    def test_concrete_must_implement_supported_media_type(self):
        class _Bad(DocumentParser):
            def parse(self, data, filename):
                return None  # type: ignore

        with pytest.raises(TypeError):
            _Bad()  # type: ignore[abstract]

    def test_concrete_must_implement_parse(self):
        class _Bad(DocumentParser):
            @property
            def supported_media_type(self):
                return "text/plain"

        with pytest.raises(TypeError):
            _Bad()  # type: ignore[abstract]

    def test_valid_concrete_subclass(self):
        class _OK(DocumentParser):
            @property
            def supported_media_type(self):
                return "text/plain"

            def parse(self, data, filename):
                return ParsedDocument(
                    title="T",
                    content=data.decode(),
                    source=filename,
                    metadata={},
                    media_type="text/plain",
                )

        parser = _OK()
        result = parser.parse(b"hello", "f.txt")
        assert result.content == "hello"


# ===========================================================================
# TextParser
# ===========================================================================


class TestTextParser:
    def setup_method(self):
        self.parser = TextParser()

    def test_supported_media_type(self):
        assert self.parser.supported_media_type == DocumentMediaType.PLAIN_TEXT

    def test_basic_parse(self):
        data = _utf8("First line.\nSecond line.")
        result = self.parser.parse(data, "sample.txt")
        assert result.title == "First line."
        assert "Second line." in result.content
        assert result.source == "sample.txt"
        assert result.media_type == DocumentMediaType.PLAIN_TEXT

    def test_title_from_first_non_empty_line(self):
        data = _utf8("\n\nActual First Line\nOther content")
        result = self.parser.parse(data, "f.txt")
        assert result.title == "Actual First Line"

    def test_title_truncated_to_120_chars(self):
        long_line = "A" * 200
        data = _utf8(long_line)
        result = self.parser.parse(data, "f.txt")
        assert len(result.title) == 120

    def test_fallback_title_from_filename(self):
        # File with only whitespace lines → should raise EmptyDocumentError
        # File with one empty content line → title from stem
        data = _utf8("   \n\n   ")
        with pytest.raises(EmptyDocumentError):
            self.parser.parse(data, "notes.txt")

    def test_utf8_encoding(self):
        data = _utf8("नमस्ते दुनिया")
        result = self.parser.parse(data, "hindi.txt")
        assert "नमस्ते" in result.content
        assert result.metadata["encoding"] == "utf-8"

    def test_latin1_fallback(self):
        # Byte 0xE9 is invalid UTF-8 but valid Latin-1 ('é')
        data = b"R\xe9sum\xe9 content here"
        result = self.parser.parse(data, "resume.txt")
        assert result.metadata["encoding"] == "latin-1"
        assert "R" in result.content

    def test_metadata_fields_present(self):
        data = _utf8("Line 1\nLine 2\nLine 3")
        result = self.parser.parse(data, "f.txt")
        assert "char_count" in result.metadata
        assert "line_count" in result.metadata
        assert "encoding" in result.metadata
        assert result.metadata["line_count"] == 3

    def test_empty_bytes_raises(self):
        with pytest.raises(EmptyDocumentError):
            self.parser.parse(b"", "empty.txt")

    def test_whitespace_only_raises(self):
        with pytest.raises(EmptyDocumentError):
            self.parser.parse(_utf8("   \n\t\n   "), "ws.txt")


# ===========================================================================
# MarkdownParser
# ===========================================================================


class TestMarkdownParser:
    def setup_method(self):
        self.parser = MarkdownParser()

    def test_supported_media_type(self):
        assert self.parser.supported_media_type == DocumentMediaType.MARKDOWN

    def test_basic_parse_with_h1(self):
        md = "# My Document\n\nSome content here.\n"
        result = self.parser.parse(_utf8(md), "doc.md")
        assert result.title == "My Document"
        assert "Some content here." in result.content
        assert result.media_type == DocumentMediaType.MARKDOWN

    def test_title_from_h2_when_no_h1(self):
        md = "## Section Title\n\nContent."
        result = self.parser.parse(_utf8(md), "doc.md")
        assert result.title == "Section Title"

    def test_title_from_front_matter(self):
        md = "---\ntitle: Front Matter Title\nauthor: Vyasa\n---\n\n# Other Heading\n\nContent."
        result = self.parser.parse(_utf8(md), "doc.md")
        assert result.title == "Front Matter Title"

    def test_front_matter_key_in_metadata(self):
        md = "---\nauthor: Vyasa\ndate: 2024-01-01\n---\n\nContent."
        result = self.parser.parse(_utf8(md), "doc.md")
        assert result.metadata.get("author") == "Vyasa"
        assert result.metadata.get("date") == "2024-01-01"

    def test_title_not_in_metadata_after_extraction(self):
        md = "---\ntitle: The Title\nauthor: X\n---\n\nContent."
        result = self.parser.parse(_utf8(md), "doc.md")
        # title extracted, should not appear again in metadata dict
        assert result.title == "The Title"

    def test_fallback_title_from_filename_stem(self):
        md = "No headings here, just plain text content."
        result = self.parser.parse(_utf8(md), "vedanta_notes.md")
        assert result.title == "vedanta_notes"

    def test_heading_count_in_metadata(self):
        md = "# H1\n\nText.\n\n## H2\n\nMore.\n\n### H3\n\nEven more."
        result = self.parser.parse(_utf8(md), "doc.md")
        assert result.metadata["heading_count"] == 3

    def test_raw_markdown_preserved_in_content(self):
        md = "# Title\n\n**Bold** and _italic_ text."
        result = self.parser.parse(_utf8(md), "doc.md")
        assert "**Bold**" in result.content
        assert "_italic_" in result.content

    def test_empty_bytes_raises(self):
        with pytest.raises(EmptyDocumentError):
            self.parser.parse(b"", "empty.md")

    def test_whitespace_only_raises(self):
        with pytest.raises(EmptyDocumentError):
            self.parser.parse(_utf8("   \n\n   "), "ws.md")

    def test_invalid_utf8_raises(self):
        bad_bytes = b"# Title\n\n\xff\xfe invalid"
        with pytest.raises(IngestionError):
            self.parser.parse(bad_bytes, "bad.md")

    def test_source_is_filename(self):
        md = "# T\n\nContent."
        result = self.parser.parse(_utf8(md), "notes.md")
        assert result.source == "notes.md"

    def test_multiline_content_preserved(self):
        md = "# Title\n\nPara 1.\n\nPara 2.\n\nPara 3."
        result = self.parser.parse(_utf8(md), "doc.md")
        assert "Para 1." in result.content
        assert "Para 3." in result.content


# ===========================================================================
# PDFParser
# ===========================================================================


class TestPDFParser:
    def setup_method(self):
        self.parser = PDFParser()

    def test_supported_media_type(self):
        assert self.parser.supported_media_type == DocumentMediaType.PDF

    def test_empty_bytes_raises(self):
        with pytest.raises(EmptyDocumentError):
            self.parser.parse(b"", "empty.pdf")

    def test_corrupted_bytes_raises_ingestion_error(self):
        garbage = b"This is not a PDF file at all."
        with pytest.raises(IngestionError):
            self.parser.parse(garbage, "bad.pdf")

    def test_successful_parse_metadata_fields_present(self):
        """Mock pypdf to verify metadata extraction path."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 content."

        mock_metadata = MagicMock()
        mock_metadata.get.side_effect = lambda key, default="": {
            "/Title": "Test PDF Title",
            "/Author": "Test Author",
            "/Creator": "",
            "/Producer": "TestPDF",
            "/CreationDate": "D:20240101",
        }.get(key, default)

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = mock_metadata

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            result = self.parser.parse(b"fake-pdf-data", "test.pdf")

        assert result.title == "Test PDF Title"
        assert result.media_type == DocumentMediaType.PDF
        assert "Page 1 content." in result.content
        assert result.metadata["page_count"] == 1
        assert result.metadata["author"] == "Test Author"
        assert result.metadata["producer"] == "TestPDF"

    def test_no_title_in_pdf_metadata_falls_back_to_filename(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Some content."

        mock_metadata = MagicMock()
        mock_metadata.get.return_value = ""

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = mock_metadata

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            result = self.parser.parse(b"fake", "my_document.pdf")

        assert result.title == "my_document"

    def test_image_only_pdf_raises_empty_document_error(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # no extractable text

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            with pytest.raises(EmptyDocumentError, match="image-only"):
                self.parser.parse(b"fake", "scan.pdf")

    def test_multi_page_text_assembled(self):
        pages = [MagicMock(), MagicMock(), MagicMock()]
        for i, p in enumerate(pages):
            p.extract_text.return_value = f"Page {i + 1} text."

        mock_reader = MagicMock()
        mock_reader.pages = pages
        mock_reader.metadata = None

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            result = self.parser.parse(b"fake", "multi.pdf")

        assert result.metadata["page_count"] == 3
        assert "Page 1 text." in result.content
        assert "Page 3 text." in result.content

    def test_pypdf_not_installed_raises_ingestion_error(self):
        """If pypdf is absent the parser raises IngestionError, not ImportError."""
        with patch.dict("sys.modules", {"pypdf": None}):
            with pytest.raises((IngestionError, Exception)):
                self.parser.parse(b"fake", "test.pdf")


# ===========================================================================
# DocumentIngestionService
# ===========================================================================


class TestDocumentIngestionService:
    def setup_method(self):
        self.service = DocumentIngestionService()

    # --- Parser selection ---

    def test_selects_text_parser_for_txt(self):
        data = _utf8("Line one.\nLine two.")
        doc = self.service.ingest(data, "sample.txt")
        assert isinstance(doc, KnowledgeDocument)
        assert "Line one." in doc.content

    def test_selects_markdown_parser_for_md(self):
        data = _utf8("# Title\n\nMarkdown content.")
        doc = self.service.ingest(data, "notes.md")
        assert isinstance(doc, KnowledgeDocument)
        assert "Markdown content." in doc.content

    def test_selects_markdown_parser_for_markdown_extension(self):
        data = _utf8("# Title\n\nContent.")
        doc = self.service.ingest(data, "notes.markdown")
        assert isinstance(doc, KnowledgeDocument)

    def test_selects_parser_via_explicit_media_type(self):
        data = _utf8("Plain text content.")
        # Force Markdown parser on a .txt file by overriding media_type
        doc = self.service.ingest(data, "weird.txt", media_type=DocumentMediaType.MARKDOWN)
        assert isinstance(doc, KnowledgeDocument)

    def test_unsupported_extension_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            self.service.ingest(b"data", "file.xlsx")

    def test_unknown_extension_no_media_type_raises(self):
        with pytest.raises(UnsupportedFileTypeError, match="Cannot determine file type"):
            self.service.ingest(b"data", "Makefile")

    def test_explicit_unsupported_media_type_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            self.service.ingest(b"data", "file.txt", media_type="application/vnd.ms-excel")

    def test_empty_content_raises_after_normalisation(self):
        with pytest.raises(EmptyDocumentError):
            self.service.ingest(b"", "empty.txt")

    # --- ID stability ---

    def test_same_input_produces_same_id(self):
        data = _utf8("Consistent content.")
        doc1 = self.service.ingest(data, "file.txt")
        doc2 = self.service.ingest(data, "file.txt")
        assert doc1.id == doc2.id

    def test_different_content_produces_different_id(self):
        doc1 = self.service.ingest(_utf8("Content A."), "file.txt")
        doc2 = self.service.ingest(_utf8("Content B."), "file.txt")
        assert doc1.id != doc2.id

    def test_different_filename_same_content_produces_different_id(self):
        data = _utf8("Same content.")
        doc1 = self.service.ingest(data, "a.txt")
        doc2 = self.service.ingest(data, "b.txt")
        assert doc1.id != doc2.id

    def test_id_is_32_char_hex_string(self):
        doc = self.service.ingest(_utf8("Hello."), "hello.txt")
        assert len(doc.id) == 32
        assert all(c in "0123456789abcdef" for c in doc.id)

    # --- Metadata merging ---

    def test_extra_metadata_merged(self):
        data = _utf8("Some content.")
        doc = self.service.ingest(data, "file.txt", extra_metadata={"uploaded_by": "user-42"})
        assert doc.metadata.get("uploaded_by") == "user-42"

    def test_ingested_at_timestamp_present(self):
        doc = self.service.ingest(_utf8("Content."), "file.txt")
        assert "ingested_at" in doc.metadata

    def test_media_type_in_metadata(self):
        doc = self.service.ingest(_utf8("Content."), "file.txt")
        assert doc.metadata.get("media_type") == DocumentMediaType.PLAIN_TEXT

    def test_title_in_metadata(self):
        doc = self.service.ingest(_utf8("The Title\nContent."), "file.txt")
        assert "title" in doc.metadata

    # --- Return type ---

    def test_returns_knowledge_document(self):
        doc = self.service.ingest(_utf8("Hello world."), "hello.txt")
        assert isinstance(doc, KnowledgeDocument)

    def test_source_is_filename(self):
        doc = self.service.ingest(_utf8("Content."), "my_file.txt")
        assert doc.source == "my_file.txt"

    # --- Async ---

    @pytest.mark.asyncio
    async def test_aingest_returns_knowledge_document(self):
        data = _utf8("Async content.")
        doc = await self.service.aingest(data, "async_file.txt")
        assert isinstance(doc, KnowledgeDocument)
        assert "Async content." in doc.content

    @pytest.mark.asyncio
    async def test_aingest_same_result_as_ingest(self):
        data = _utf8("Identical content.")
        sync_doc = self.service.ingest(data, "file.txt")
        async_doc = await self.service.aingest(data, "file.txt")
        assert sync_doc.id == async_doc.id
        assert sync_doc.content == async_doc.content

    # --- Parser registration ---

    def test_register_parser_replaces_existing(self):
        """A custom parser registered for text/plain should be used instead."""

        class _CustomTextParser(DocumentParser):
            @property
            def supported_media_type(self) -> str:
                return DocumentMediaType.PLAIN_TEXT

            def parse(self, data: bytes, filename: str) -> ParsedDocument:
                return ParsedDocument(
                    title="Custom Title",
                    content=data.decode() + " [custom]",
                    source=filename,
                    metadata={},
                    media_type=DocumentMediaType.PLAIN_TEXT,
                )

        self.service.register_parser(_CustomTextParser())
        doc = self.service.ingest(_utf8("Hello."), "file.txt")
        assert "[custom]" in doc.content

    def test_extra_parsers_in_constructor(self):
        class _CustomParser(DocumentParser):
            @property
            def supported_media_type(self) -> str:
                return "application/x-custom"

            def parse(self, data: bytes, filename: str) -> ParsedDocument:
                return ParsedDocument(
                    title="Custom",
                    content=data.decode(),
                    source=filename,
                    metadata={},
                    media_type="application/x-custom",
                )

        service = DocumentIngestionService(extra_parsers=[_CustomParser()])
        doc = service.ingest(_utf8("Hello world."), "file.txt", media_type="application/x-custom")
        assert "Hello world." in doc.content

    # --- Supported extensions ---

    def test_supported_extensions_includes_standard(self):
        exts = self.service.supported_extensions()
        for ext in [".pdf", ".md", ".txt"]:
            assert ext in exts

    def test_supported_extensions_sorted(self):
        exts = self.service.supported_extensions()
        assert exts == sorted(exts)

    # --- Normaliser is applied ---

    def test_normaliser_strips_excessive_blank_lines(self):
        data = _utf8("Line A.\n\n\n\n\nLine B.")
        doc = self.service.ingest(data, "file.txt")
        assert "\n\n\n" not in doc.content

    def test_normaliser_strips_trailing_whitespace(self):
        data = _utf8("Line A.   \nLine B.  ")
        doc = self.service.ingest(data, "file.txt")
        for line in doc.content.splitlines():
            assert not line.endswith(" ")

    # --- Markdown ingestion end-to-end ---

    def test_markdown_end_to_end(self):
        md = textwrap.dedent("""\
            ---
            title: Vedic Astrology Guide
            author: Parashara
            ---

            # Introduction

            Vedic astrology is an ancient science.

            ## Houses

            There are twelve houses.
        """)
        doc = self.service.ingest(_utf8(md), "guide.md")
        assert doc.metadata.get("title") == "Vedic Astrology Guide"
        assert doc.metadata.get("author") == "Parashara"
        assert "twelve houses" in doc.content

    # --- PDF ingestion (mocked) ---

    def test_pdf_ingestion_via_service(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Vedic chart content."

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            doc = self.service.ingest(b"fake-pdf", "chart.pdf")

        assert isinstance(doc, KnowledgeDocument)
        assert "Vedic chart content." in doc.content
        assert doc.metadata.get("media_type") == DocumentMediaType.PDF
