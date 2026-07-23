from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.message import Message


class MessageRepository:
    """
    Repository for managing Message data access.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """
        Retrieve a message by its primary key.
        """
        return await self._db.get(Message, message_id)

    async def list_by_conversation(self, conversation_id: UUID) -> Sequence[Message]:
        """
        List all messages for a specific conversation, ordered by created_at.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def create(self, conversation_id: UUID, role: str, content: str) -> Message:
        """
        Create a new message record.
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self._db.add(message)
        await self._db.commit()
        await self._db.refresh(message)
        return message
