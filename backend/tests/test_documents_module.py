import io
import zipfile
import pytest
import shutil
import tempfile
import asyncio
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db.models.user import User
from app.db.models.document import Document
from app.db.repositories.document_repository import DocumentRepository
from app.domain.rag import KnowledgeDocument, KnowledgeChunk, RetrievedChunk, VectorStoreException
from app.services.document_ingestion import DocumentIngestionService, DOCXParser, DocumentMediaType
from app.services.rag.providers.chroma_vector_store import ChromaVectorStore
from app.services.rag.retriever import DefaultKnowledgeRetriever
from app.services.document_service import DocumentService, DocumentAlreadyExistsException, DocumentNotFoundException
from app.core.config import settings


# ---------------------------------------------------------------------------
# DOCX Parser Tests
# ---------------------------------------------------------------------------

def generate_mock_docx(text: str) -> bytes:
    """Generate a minimal valid zip representation of a .docx file."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as docx:
        xml_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:t>{text}</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </w:document>"""
        docx.writestr("word/document.xml", xml_content.encode("utf-8"))
    return buffer.getvalue()


def test_docx_parser():
    parser = DOCXParser()
    assert parser.supported_media_type == DocumentMediaType.DOCX

    docx_data = generate_mock_docx("Hello world from JyotishAI!")
    parsed = parser.parse(docx_data, "test.docx")

    assert parsed.title == "test"
    assert parsed.content == "Hello world from JyotishAI!"
    assert parsed.media_type == DocumentMediaType.DOCX
    assert parsed.metadata["char_count"] == len("Hello world from JyotishAI!")
    assert parsed.metadata["paragraph_count"] == 1


# ---------------------------------------------------------------------------
# Vector Store Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_chroma_vector_store():
    # Create a temporary directory for Chroma DB
    temp_dir = tempfile.mkdtemp()
    try:
        # Ensure local PersistentClient path is used (not an HTTP server connection)
        with patch.object(settings, "CHROMA_HOST", None), patch.object(settings, "CHROMA_PORT", None):
            store = ChromaVectorStore(persist_directory=temp_dir, collection_name="test_collection")
        assert store.store_name == "test_collection"

        # Count initially
        assert await store.count() == 0

        # Upsert chunks
        chunks = [
            KnowledgeChunk(id="c1", document_id="doc1", content="Rig Veda content.", chunk_index=0),
            KnowledgeChunk(id="c2", document_id="doc1", content="Sama Veda content.", chunk_index=1),
        ]
        # Use distinct directions in cosine space
        emb1 = [0.0] * 768
        emb1[0] = 1.0
        emb2 = [0.0] * 768
        emb2[1] = 1.0
        embeddings = [emb1, emb2]

        await store.upsert(chunks, embeddings)
        assert await store.count() == 2

        # Exists check
        assert await store.exists("c1") is True
        assert await store.exists("c3") is False

        # Query
        results = await store.query(query_embedding=emb1, top_k=1)
        assert len(results) == 1
        assert results[0].id == "c1"

        # Delete
        await store.delete(["c1"])
        assert await store.count() == 1
        assert await store.exists("c1") is False

    finally:
        # Stop Chroma client to release file handles before deleting directory
        if 'store' in locals() and hasattr(store, '_client') and hasattr(store._client, '_system'):
            try:
                store._client._system.stop()
            except Exception:
                pass
        # Cleanup temporary files
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Repository & Service Tests (Async SQLite in-memory DB)
# ---------------------------------------------------------------------------

@pytest.fixture
async def async_db():
    # Use a shared in-memory SQLite database (via StaticPool) so that the test
    # session and the background-task session (which imports the patched
    # AsyncSessionLocal from app.db.session) see each other's committed writes.
    from sqlalchemy.pool import StaticPool
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, expire_on_commit=True, class_=AsyncSession)

    async with engine.begin() as conn:
        # Recreate tables
        await conn.run_sync(Base.metadata.create_all)

    # Patch the production AsyncSessionLocal so that background tasks
    # (which import it from app.db.session) use this test DB instead of
    # attempting to connect to the real PostgreSQL database. We make it
    # return the test session itself so writes are immediately visible.
    import app.db.session as _db_session
    _original_asl = _db_session.AsyncSessionLocal

    # The yielded session; the patch below will hand this same session
    # back so the background task shares the test transaction.
    _test_session_holder = {}

    def _shared_session_factory():
        return _test_session_holder["session"]

    _db_session.AsyncSessionLocal = _shared_session_factory
    try:
        async with async_session() as session:
            _test_session_holder["session"] = session
            yield session
    finally:
        _db_session.AsyncSessionLocal = _original_asl

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.anyio
async def test_document_repository_and_service(async_db: AsyncSession):
    # 1. Create a dummy user
    user_id = uuid4()
    dummy_user = User(
        id=user_id,
        email="test_rag@jyotish.ai",
        username="rag_tester",
        hashed_password="securepassword"
    )
    async_db.add(dummy_user)
    await async_db.commit()

    # 2. Setup repos & service mocks
    repo = DocumentRepository(async_db)
    mock_retriever = AsyncMock()
    service = DocumentService(repo, mock_retriever)

    docx_data = generate_mock_docx("Astrological interpretation of birth charts.")
    bg_tasks = BackgroundTasks()

    # 3. Test Upload Document
    doc = await service.upload_document(
        filename="birth_reading.docx",
        data=docx_data,
        user_id=user_id,
        background_tasks=bg_tasks
    )

    assert doc.id is not None
    assert doc.filename == "birth_reading.docx"
    assert doc.media_type == DocumentMediaType.DOCX
    assert doc.status == "pending"
    assert doc.user_id == user_id

    # Duplicate upload check
    with pytest.raises(DocumentAlreadyExistsException):
        await service.upload_document(
            filename="birth_reading.docx",
            data=docx_data,
            user_id=user_id,
            background_tasks=bg_tasks
        )

    # 4. Test List Documents
    docs, total = await service.list_documents(user_id=user_id)
    assert total == 1
    assert docs[0].id == doc.id

    # 5. Run the background processor synchronously to test complete pipeline
    await service._process_document_background(
        doc_id=doc.id,
        data=docx_data,
        filename="birth_reading.docx",
        user_id=user_id
    )

    # Reload document to verify changes
    updated_doc = await service.get_document(doc.id, user_id)
    assert updated_doc.status == "completed"
    assert "Astrological interpretation" in updated_doc.content
    assert updated_doc.metadata_json is not None
    assert updated_doc.metadata_json["media_type"] == DocumentMediaType.DOCX

    # Check retriever was called
    assert mock_retriever.ingest.called

    # 6. Test Preview
    preview = await service.get_preview(doc.id, user_id, max_chars=10)
    assert len(preview) <= 10

    # 7. Test Delete
    success = await service.delete_document(doc.id, user_id)
    assert success is True

    # Confirm it's gone
    with pytest.raises(DocumentNotFoundException):
        await service.get_document(doc.id, user_id)
