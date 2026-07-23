from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.conversation import Conversation


class ConversationRepository:
    """
    Repository for managing Conversation data access.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Retrieve a conversation by its primary key.
        Eagerly loads messages.
        """
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: Optional[UUID], limit: int = 20, offset: int = 0, search: Optional[str] = None
    ) -> Sequence[Conversation]:
        """
        List conversations for a user (or all if user_id is None) with pagination.
        Ordered by updated_at descending.
        """
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
        )
        if search:
            stmt = stmt.where(Conversation.title.ilike(f"%{search}%"))
        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def create(self, user_id: Optional[UUID] = None, title: str = "New Conversation") -> Conversation:
        """
        Create a new conversation.
        """
        conversation = Conversation(user_id=user_id, title=title)
        self._db.add(conversation)
        await self._db.commit()
        await self._db.refresh(conversation)
        return conversation

    async def update_title(self, conversation_id: UUID, title: str) -> Optional[Conversation]:
        """
        Update the title of a conversation.
        """
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return None
        conversation.title = title
        await self._db.commit()
        await self._db.refresh(conversation)
        return conversation

    async def delete(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation record. Cascade delete handles its messages.
        """
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return False
        await self._db.delete(conversation)
        await self._db.commit()
        return True

    async def touch_updated_at(self, conversation: "Conversation") -> None:
        """
        Persist a change to conversation.updated_at without reloading the object.

        The caller is responsible for setting ``conversation.updated_at`` before
        invoking this method; the repository only commits the open transaction.
        This keeps the ``_db`` session private to the repository layer.
        """
        await self._db.commit()
