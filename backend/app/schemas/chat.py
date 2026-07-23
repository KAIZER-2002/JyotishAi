from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.astrology import BirthChartRequest
from uuid import UUID


class LLMUsageSchema(BaseModel):
    prompt_tokens: int = Field(..., description="Number of prompt tokens used")
    completion_tokens: int = Field(..., description="Number of completion tokens used")
    total_tokens: int = Field(..., description="Total tokens used")


class ChatRequest(BaseModel):
    """Request schema for the astrology AI chat endpoint."""
    user_query: str = Field(..., description="The question or focus area for the reading")
    birth_data: BirthChartRequest = Field(..., description="The birth details for chart calculation")
    conversation_id: Optional[UUID] = Field(None, description="Optional ID of an existing conversation thread")


class ChatResponse(BaseModel):
    """Response schema for the astrology AI chat endpoint."""
    response: str = Field(..., description="The AI generated response text")
    provider: str = Field(..., description="The LLM provider name")
    model: str = Field(..., description="The model name")
    finish_reason: str = Field(..., description="Why generation ended (e.g. 'stop', 'length')")
    usage: Optional[LLMUsageSchema] = Field(None, description="Token usage details")
    conversation_id: Optional[UUID] = Field(None, description="The ID of the conversation thread associated with this chat turn")


class StreamChunk(BaseModel):
    """A single chunk in a server-sent events streaming response."""
    text: str = Field(..., description="Partial text chunk from the LLM")
    finish_reason: Optional[str] = Field(None, description="Set on the final chunk when streaming ends")
    conversation_id: Optional[UUID] = Field(None, description="The conversation ID — present on every chunk")
