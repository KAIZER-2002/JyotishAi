from typing import Annotated, Optional
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.db.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService, DocumentAlreadyExistsException, DocumentNotFoundException
from app.services.rag.providers.gemini_embedding_provider import GeminiEmbeddingProvider
from app.services.rag.providers.chroma_vector_store import ChromaVectorStore
from app.services.rag.retriever import DefaultKnowledgeRetriever
from app.core.config import settings
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentPreviewResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

CurrentUser = Annotated[User, Depends(get_current_user)]

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}


def _build_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Dependency: constructs DocumentService with real Chroma DB and repositories."""
    repo = DocumentRepository(db)
    embedding_provider = GeminiEmbeddingProvider()
    vector_store = ChromaVectorStore(persist_directory=settings.CHROMA_PERSIST_DIR)
    retriever = DefaultKnowledgeRetriever(embedding_provider, vector_store)
    return DocumentService(repo, retriever)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document to knowledge base",
    description="Uploads a PDF, DOCX, TXT, or Markdown document to parse, chunk, embed and ingest it.",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    document_service: DocumentService = Depends(_build_document_service),
) -> DocumentResponse:
    """
    Endpoint to upload a raw file, validate type, create database records and trigger parsing in the background.
    """
    filename = file.filename or "document"
    ext = Path(filename).suffix.lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only {', '.join(SUPPORTED_EXTENSIONS)} are supported."
        )

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )
        
        MAX_UPLOAD_SIZE = 15 * 1024 * 1024  # 15 MB
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the {MAX_UPLOAD_SIZE // (1024 * 1024)}MB limit."
            )

        doc = await document_service.upload_document(
            filename=filename,
            data=content,
            user_id=current_user.id,
            background_tasks=background_tasks
        )
        return doc
    except DocumentAlreadyExistsException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(exc)}"
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List documents",
    description="Returns a paginated list of documents with optional sorting, search and media_type filter.",
)
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    search: Optional[str] = None,
    media_type: Optional[str] = None,
    current_user: CurrentUser = None,
    document_service: DocumentService = Depends(_build_document_service),
) -> DocumentListResponse:
    """
    Endpoint to list the user's documents.
    """
    allowed_sort_fields = {"created_at", "filename", "size_bytes", "status"}
    if sort_by not in allowed_sort_fields:
        sort_by = "created_at"

    docs, total = await document_service.list_documents(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        media_type=media_type
    )
    return DocumentListResponse(documents=list(docs), total_count=total)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document details",
    description="Returns the details and processing status of an uploaded document.",
)
async def get_document(
    document_id: str,
    current_user: CurrentUser = None,
    document_service: DocumentService = Depends(_build_document_service),
) -> DocumentResponse:
    """
    Endpoint to retrieve metadata for a single document.
    """
    try:
        return await document_service.get_document(document_id, current_user.id)
    except DocumentNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )


@router.get(
    "/{document_id}/preview",
    response_model=DocumentPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview document content",
    description="Returns a truncated text preview of the parsed document content.",
)
async def get_document_preview(
    document_id: str,
    current_user: CurrentUser = None,
    document_service: DocumentService = Depends(_build_document_service),
) -> DocumentPreviewResponse:
    """
    Endpoint to retrieve a text content preview.
    """
    try:
        doc = await document_service.get_document(document_id, current_user.id)
        preview = await document_service.get_preview(document_id, current_user.id)
        return DocumentPreviewResponse(
            id=doc.id,
            filename=doc.filename,
            content_preview=preview
        )
    except DocumentNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Deletes the document tracking record and all its ingested vector chunks.",
)
async def delete_document(
    document_id: str,
    current_user: CurrentUser = None,
    document_service: DocumentService = Depends(_build_document_service),
) -> None:
    """
    Endpoint to delete a document and clean up vectors.
    """
    try:
        await document_service.delete_document(document_id, current_user.id)
    except DocumentNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
