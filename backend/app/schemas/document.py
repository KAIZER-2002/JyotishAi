from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List


class DocumentResponse(BaseModel):
    """
    Pydantic response schema representing document tracking record.
    """
    id: str
    filename: str
    media_type: str
    size_bytes: int
    status: str
    error_message: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """
    Pydantic schema representing paginated list response of documents.
    """
    documents: List[DocumentResponse]
    total_count: int


class DocumentPreviewResponse(BaseModel):
    """
    Pydantic schema representing the document text preview.
    """
    id: str
    filename: str
    content_preview: str
