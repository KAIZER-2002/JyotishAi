from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService, ConversationNotFoundException
from app.api.deps import get_current_user, get_current_user_optional
from app.db.models.user import User
from app.schemas.conversation import (
    ConversationResponseSchema,
    ConversationListItemSchema,
    ConversationRenameRequest,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


async def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    """Dependency to provide a ConversationService instance."""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    return ConversationService(conv_repo, msg_repo)


from app.api.deps import get_current_user, get_current_user_optional

@router.get("", response_model=List[ConversationListItemSchema], status_code=status.HTTP_200_OK)
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    conv_service: ConversationService = Depends(get_conversation_service),
) -> List[ConversationListItemSchema]:
    """
    Get paginated conversations for the current authenticated user (or guest sessions).
    Can filter by title with optional search term.
    """
    user_id = current_user.id if current_user else None
    conversations = await conv_service.list_conversations(
        user_id=user_id, limit=limit, offset=offset, search=search
    )
    return list(conversations)


@router.get("/{conversation_id}", response_model=ConversationResponseSchema, status_code=status.HTTP_200_OK)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponseSchema:
    """
    Retrieve details of a single conversation with full message history.
    """
    try:
        conversation = await conv_service.get_conversation(conversation_id)
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return conversation
    except ConversationNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )


@router.patch("/{conversation_id}", response_model=ConversationListItemSchema, status_code=status.HTTP_200_OK)
async def rename_conversation(
    conversation_id: UUID,
    request: ConversationRenameRequest,
    current_user: User = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
) -> ConversationListItemSchema:
    """
    Rename the title of a specific conversation.
    """
    try:
        # Verify ownership first
        conversation = await conv_service.get_conversation(conversation_id)
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return await conv_service.rename_conversation(conversation_id, request.title)
    except ConversationNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
) -> None:
    """
    Delete a conversation thread.
    """
    try:
        # Verify ownership first
        conversation = await conv_service.get_conversation(conversation_id)
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        await conv_service.delete_conversation(conversation_id)
    except ConversationNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
