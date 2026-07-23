from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User


class UserRepository:
    """
    Repository for managing User data access.
    
    Encapsulates all SQLAlchemy queries for the User model to decouple 
    the service layer from the database implementation details.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Retrieve a user by their primary key.
        """
        result = await self._db.get(User, user_id)
        return result

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their unique email address.
        """
        stmt = select(User).where(User.email == email)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by their unique username.
        """
        stmt = select(User).where(User.username == username)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_email(self, email: str) -> bool:
        """
        Check if a user with the given email already exists.
        """
        stmt = select(User.id).where(User.email == email).limit(1)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_username(self, username: str) -> bool:
        """
        Check if a user with the given username already exists.
        """
        stmt = select(User.id).where(User.username == username).limit(1)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, user_data: dict) -> User:
        """
        Create a new user record.
        
        Args:
            user_data: Dictionary containing user fields.
            
        Returns:
            The created User model instance.
        """
        user = User(**user_data)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def update(self, user_id: UUID, update_data: dict) -> Optional[User]:
        """
        Update an existing user record.
        
        Args:
            user_id: The UUID of the user to update.
            update_data: Dictionary of fields to update.
            
        Returns:
            The updated User model instance, or None if not found.
        """
        # Fetch the user first to ensure they exist and to apply updates to the object
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            setattr(user, key, value)
            
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete a user record.
        
        Returns:
            True if the user was deleted, False otherwise.
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self._db.delete(user)
        await self._db.commit()
        return True
