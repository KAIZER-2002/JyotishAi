from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class MessageResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    created_at: datetime

class ConversationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponseSchema] = []

class ConversationListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

class ConversationRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
