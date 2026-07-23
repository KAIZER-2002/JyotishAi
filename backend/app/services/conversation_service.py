from typing import Optional, Sequence
from datetime import datetime, timezone
from uuid import UUID
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.db.models.conversation import Conversation
from app.db.models.message import Message


class ConversationServiceException(Exception):
    """Base exception for conversation service errors."""
    pass


class ConversationNotFoundException(ConversationServiceException):
    """Raised when a requested conversation cannot be found."""
    pass


class ConversationService:
    """
    Service layer for managing chat conversation business logic.
    """

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
    ) -> None:
        self._conversation_repo = conversation_repository
        self._message_repo = message_repository

    async def create_conversation(
        self, user_id: Optional[UUID] = None, title: Optional[str] = None
    ) -> Conversation:
        """
        Creates a new conversation.
        """
        conv_title = title if title and title.strip() else "New Conversation"
        return await self._conversation_repo.create(user_id=user_id, title=conv_title)

    async def get_conversation(self, conversation_id: UUID) -> Conversation:
        """
        Retrieve a conversation by its ID. Eagerly loads messages.
        
        Raises:
            ConversationNotFoundException: If no conversation is found.
        """
        conversation = await self._conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ConversationNotFoundException(f"Conversation with ID {conversation_id} not found.")
        return conversation

    async def list_conversations(
        self, user_id: Optional[UUID], limit: int = 20, offset: int = 0, search: Optional[str] = None
    ) -> Sequence[Conversation]:
        """
        List conversations for a user with pagination.
        """
        return await self._conversation_repo.list_by_user(
            user_id=user_id, limit=limit, offset=offset, search=search
        )

    async def rename_conversation(self, conversation_id: UUID, title: str) -> Conversation:
        """
        Rename an existing conversation.
        
        Raises:
            ConversationNotFoundException: If the conversation does not exist.
        """
        if not title or not title.strip():
            raise ConversationServiceException("Conversation title cannot be empty.")
            
        conversation = await self._conversation_repo.update_title(conversation_id, title.strip())
        if not conversation:
            raise ConversationNotFoundException(f"Conversation with ID {conversation_id} not found.")
        return conversation

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation.
        
        Raises:
            ConversationNotFoundException: If the conversation does not exist.
        """
        deleted = await self._conversation_repo.delete(conversation_id)
        if not deleted:
            raise ConversationNotFoundException(f"Conversation with ID {conversation_id} not found.")
        return True

    async def append_message(self, conversation_id: UUID, role: str, content: str) -> Message:
        """
        Append a new message (user or assistant) to a conversation.
        
        Raises:
            ConversationNotFoundException: If the conversation does not exist.
        """
        if not role or not role.strip():
            raise ConversationServiceException("Message role cannot be empty.")
        if not content or not content.strip():
            raise ConversationServiceException("Message content cannot be empty.")

        # Verify conversation exists first
        conversation = await self._conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ConversationNotFoundException(f"Conversation with ID {conversation_id} not found.")

        # Create message
        message = await self._message_repo.create(
            conversation_id=conversation_id,
            role=role.strip(),
            content=content.strip(),
        )

        conversation.updated_at = datetime.now(timezone.utc)
        await self._conversation_repo.touch_updated_at(conversation)
        return message
