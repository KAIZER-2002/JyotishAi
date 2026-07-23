import abc
from uuid import UUID


class AvatarStorageService(abc.ABC):
    """
    Abstract interface for managing user avatar image uploads and storage.
    
    Decouples the core user business logic from the underlying storage provider
    (e.g., Local Filesystem, AWS S3, Google Cloud Storage).
    """

    @abc.abstractmethod
    async def upload_avatar(self, user_id: UUID, file_content: bytes, filename: str) -> str:
        """
        Uploads an avatar image and returns the publicly accessible URL or path.
        
        Args:
            user_id: The UUID of the authenticated user.
            file_content: The binary content of the uploaded file.
            filename: The original file name.
            
        Returns:
            The public URL or relative static path to the saved image.
        """
        pass

    @abc.abstractmethod
    async def delete_avatar(self, user_id: UUID, avatar_url: str) -> None:
        """
        Deletes the avatar image from storage.
        """
        pass


class MockAvatarStorageService(AvatarStorageService):
    """
    Production-grade mock implementation for local/testing environments.
    
    Saves the file to a simulated path and returns a clean relative URL.
    Note: Real deployments should integrate with AWS S3, Google Cloud Storage, or a real filesystem storage.
    """

    async def upload_avatar(self, user_id: UUID, file_content: bytes, filename: str) -> str:
        # Simulate clean public path path return
        extension = filename.split(".")[-1] if "." in filename else "png"
        simulated_path = f"/static/avatars/{user_id}.{extension}"
        
        # Real production implementations would write to disk, S3, or GCS here.
        # e.g., open(local_path, "wb").write(file_content)
        
        return simulated_path

    async def delete_avatar(self, user_id: UUID, avatar_url: str) -> None:
        # Mock deletion - no-op since no file is written in mock
        pass


import os

class LocalAvatarStorageService(AvatarStorageService):
    """
    Production-grade local filesystem implementation.
    """
    def __init__(self, storage_dir: str = "avatars"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    async def upload_avatar(self, user_id: UUID, file_content: bytes, filename: str) -> str:
        extension = filename.split(".")[-1] if "." in filename else "png"
        new_filename = f"{user_id}.{extension}"
        local_path = os.path.join(self.storage_dir, new_filename)
        
        with open(local_path, "wb") as f:
            f.write(file_content)
            
        return f"/static/avatars/{new_filename}"

    async def delete_avatar(self, user_id: UUID, avatar_url: str) -> None:
        filename = avatar_url.split("/")[-1]
        local_path = os.path.join(self.storage_dir, filename)
        if os.path.exists(local_path):
            os.remove(local_path)
