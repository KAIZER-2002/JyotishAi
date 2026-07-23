from typing import Optional, Sequence, Dict, Any
from uuid import UUID
from sqlalchemy import select, update, delete, desc, asc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.document import Document


class DocumentRepository:
    """
    Repository for managing Document data access.
    
    Encapsulates all SQLAlchemy queries for the Document model.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id_and_user_id(self, document_id: str, user_id: UUID) -> Optional[Document]:
        """
        Retrieve a document by ID and owner's user ID.
        """
        stmt = select(Document).where(
            and_(
                Document.id == document_id,
                Document.user_id == user_id
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
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
        List, sort, search, and paginate documents for a specific user.
        
        Returns:
            A tuple of (documents, total_count).
        """
        # Base query
        base_filters = [Document.user_id == user_id]

        if media_type:
            base_filters.append(Document.media_type == media_type)

        if search:
            base_filters.append(Document.filename.ilike(f"%{search}%"))

        # Total count query
        count_stmt = select(Document.id).where(and_(*base_filters))
        count_res = await self._db.execute(count_stmt)
        total_count = len(count_res.scalars().all())

        # Select query
        stmt = select(Document).where(and_(*base_filters))

        # Apply sorting
        sort_attr = getattr(Document, sort_by, Document.created_at)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(asc(sort_attr))
        else:
            stmt = stmt.order_by(desc(sort_attr))

        # Pagination
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self._db.execute(stmt)
        documents = result.scalars().all()
        return documents, total_count

    async def create(self, document_data: dict[str, Any]) -> Document:
        """
        Create a new document tracking record.
        """
        document = Document(**document_data)
        self._db.add(document)
        await self._db.commit()
        await self._db.refresh(document)
        return document

    async def update(self, document_id: str, user_id: UUID, update_data: dict[str, Any]) -> Optional[Document]:
        """
        Update fields on an existing document record.
        """
        document = await self.get_by_id_and_user_id(document_id, user_id)
        if not document:
            return None

        for key, value in update_data.items():
            setattr(document, key, value)

        await self._db.commit()
        await self._db.refresh(document)
        return document

    async def update_status(
        self,
        document_id: str,
        user_id: UUID,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Document]:
        """
        Update the processing status of a document.
        """
        update_data = {"status": status}
        if error_message is not None:
            update_data["error_message"] = error_message
        
        return await self.update(document_id, user_id, update_data)

    async def delete(self, document_id: str, user_id: UUID) -> bool:
        """
        Delete a document record.
        """
        document = await self.get_by_id_and_user_id(document_id, user_id)
        if not document:
            return False

        await self._db.delete(document)
        await self._db.commit()
        return True
