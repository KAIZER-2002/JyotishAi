import asyncio
from app.db.session import AsyncSessionLocal
from app.services.document_service import DocumentService
from app.services.document_ingestion import DocumentIngestionService
from app.db.models.user import User
from sqlalchemy import select

class DummyBackgroundTasks:
    def add_task(self, func, *args, **kwargs):
        asyncio.create_task(func(*args, **kwargs))

async def run():
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User))).scalars().first()
        print("Testing ingestion for user:", user.email)
        service = DocumentService(session)
        bg = DummyBackgroundTasks()
        doc = await service.upload_document(
            filename="test_report.txt",
            data=b"Astro Report: Jupiter in 9th house brings wisdom and spiritual growth.",
            user_id=user.id,
            background_tasks=bg
        )
        print("Doc ID:", doc.id, "Initial Status:", doc.status)
        await asyncio.sleep(4)
        doc_updated = await service.get_document(doc.id, user.id)
        print("Final Status:", doc_updated.status, "Error Message:", doc_updated.error_message)

if __name__ == "__main__":
    asyncio.run(run())

