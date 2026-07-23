import asyncio
from uuid import UUID
from typing import Optional, Sequence, Any
from app.db.repositories.document_repository import DocumentRepository
from app.domain.rag import KnowledgeRetriever, KnowledgeDocument, KnowledgeChunk
from app.services.document_ingestion import DocumentIngestionService, DocumentMediaType
from app.services.chunking import ChunkingService, ChunkingConfig, HeadingAwareChunker, FixedSizeChunker
from app.db.models.document import Document


class DocumentAlreadyExistsException(Exception):
    """Raised when a document with the same content hash is uploaded by the user."""
    pass


class DocumentNotFoundException(Exception):
    """Raised when a document is not found."""
    pass


class DocumentService:
    """
    Orchestrates the ingestion, chunking, embedding, vector storage,
    and metadata tracking of user documents.
    """

    def __init__(self, repository: DocumentRepository, retriever: KnowledgeRetriever) -> None:
        self.repository = repository
        self.retriever = retriever

    async def get_document(self, document_id: str, user_id: UUID) -> Document:
        """
        Get details of a specific document for a user.
        """
        doc = await self.repository.get_by_id_and_user_id(document_id, user_id)
        if not doc:
            raise DocumentNotFoundException(f"Document with ID '{document_id}' not found.")
        return doc

    async def list_documents(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> tuple[Sequence[Document], int]:
        """
        List user's documents.
        """
        return await self.repository.list_for_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            media_type=media_type
        )

    async def upload_document(self, filename: str, data: bytes, user_id: UUID, background_tasks: Any) -> Document:
        """
        Register a new document in the relational DB and schedule ingestion processing in the background.
        """
        # 1. Generate content-addressed ID (SHA-256)
        doc_id = DocumentIngestionService._make_id(data, filename)

        # 2. Check for duplicate upload
        existing = await self.repository.get_by_id_and_user_id(doc_id, user_id)
        if existing:
            raise DocumentAlreadyExistsException("This document has already been uploaded.")

        # 3. Create document tracking entry in "pending" status
        media_type = DocumentMediaType.from_filename(filename) or "application/octet-stream"
        doc = await self.repository.create({
            "id": doc_id,
            "filename": filename,
            "media_type": media_type,
            "size_bytes": len(data),
            "status": "pending",
            "user_id": user_id,
        })

        # 4. Enqueue the background processing task
        background_tasks.add_task(self._process_document_background, doc_id, data, filename, user_id)

        return doc

    async def delete_document(self, document_id: str, user_id: UUID) -> bool:
        """
        Deletes a document from the database and deletes its associated vector chunks from Chroma.
        """
        doc = await self.repository.get_by_id_and_user_id(document_id, user_id)
        if not doc:
            raise DocumentNotFoundException(f"Document with ID '{document_id}' not found.")

        # 1. Delete associated chunks from Chroma
        # We fetch the chunk IDs from Chroma first using the metadata filter, then delete them.
        if hasattr(self.retriever, "vector_store") and hasattr(self.retriever.vector_store, "_collection"):
            def _sync_get_chunk_ids():
                collection = self.retriever.vector_store._collection
                res = collection.get(where={"document_id": document_id})
                return res.get("ids", [])

            try:
                chunk_ids = await asyncio.to_thread(_sync_get_chunk_ids)
                if chunk_ids:
                    await self.retriever.vector_store.delete(chunk_ids)
            except Exception as e:
                # Soft failure: log and continue deleting the db record
                pass

        # 2. Delete document tracking entry from PostgreSQL
        return await self.repository.delete(document_id, user_id)

    async def get_preview(self, document_id: str, user_id: UUID, max_chars: int = 5000) -> str:
        """
        Retrieve a truncated text preview of the document.
        """
        doc = await self.get_document(document_id, user_id)
        if not doc.content:
            if doc.status == "processing" or doc.status == "pending":
                return "[Document is still processing...]"
            return "[No text content available]"
        
        return doc.content[:max_chars]

    async def _process_document_background(self, doc_id: str, data: bytes, filename: str, user_id: UUID) -> None:
        """
        FastAPI background task callback to parse, chunk, embed, and store document segments.
        """
        from app.db.session import AsyncSessionLocal
        from app.db.repositories.document_repository import DocumentRepository

        async with AsyncSessionLocal() as session:
            repository = DocumentRepository(session)
            try:
                # 1. Update status to processing
                await repository.update_status(doc_id, user_id, "processing")
    
                # 2. Ingest / Parse document text
                ingestion_service = DocumentIngestionService()
                know_doc = await ingestion_service.aingest(
                    data=data,
                    filename=filename,
                    extra_metadata={"user_id": str(user_id)}
                )
    
                # Update document content and metadata in PostgreSQL
                await repository.update(doc_id, user_id, {
                    "content": know_doc.content,
                    "metadata_json": know_doc.metadata,
                })
    
                # 3. Chunk the document content
                is_md = know_doc.metadata.get("media_type") == DocumentMediaType.MARKDOWN
                strategy = HeadingAwareChunker() if is_md else FixedSizeChunker()
                chunking_service = ChunkingService(strategy)
    
                config = ChunkingConfig(chunk_size=500, chunk_overlap=50)
                chunks = await chunking_service.achunk_document(know_doc, config)
    
                # 4. Embed chunks and index into vector store
                await self.retriever.ingest(chunks)
    
                # 5. Mark document as completed
                await repository.update_status(doc_id, user_id, "completed")
            except Exception as e:
                # Mark document as failed and persist the error message
                await repository.update_status(doc_id, user_id, "failed", error_message=str(e))
