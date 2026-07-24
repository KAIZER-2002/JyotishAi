import asyncio
from app.db.session import AsyncSessionLocal
from app.services.document_service import DocumentService
from app.services.rag.retriever import DefaultKnowledgeRetriever
from app.services.rag.providers.chroma_vector_store import ChromaVectorStore
from app.services.rag.providers.gemini_embedding_provider import GeminiEmbeddingProvider
from app.db.repositories.document_repository import DocumentRepository
from app.core.config import settings
from app.db.models.user import User
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User))).scalars().first()
        print("Testing background processing for user:", user.email)
        
        repo = DocumentRepository(session)
        embed_provider = GeminiEmbeddingProvider()
        vector_store = ChromaVectorStore(persist_directory=settings.CHROMA_PERSIST_DIR)
        retriever = DefaultKnowledgeRetriever(embed_provider, vector_store)
        service = DocumentService(repo, retriever)
        
        class DummyBG:
            def add_task(self, func, *args, **kwargs):
                pass

        doc = await service.upload_document(
            filename="test_vedic_astrology.txt",
            data=b"Vedic Astrology: The 10th house governs career, status, and public reputation. Saturn placed in 10th house creates discipline.",
            user_id=user.id,
            background_tasks=DummyBG()
        )
        print("Document created with ID:", doc.id, "Initial status:", doc.status)
        
        # Manually run background processing
        await service._process_document_background(
            doc.id,
            b"Vedic Astrology: The 10th house governs career, status, and public reputation. Saturn placed in 10th house creates discipline.",
            "test_vedic_astrology.txt",
            user.id
        )
        
        doc_updated = await service.repository.get_by_id_and_user_id(doc.id, user.id)
        if doc_updated:
            print("Processing finished!")
            print("Final Status:", doc_updated.status)
            print("Error Message:", doc_updated.error_message)
            print("Content Preview:", doc_updated.content[:60] if doc_updated.content else None)

if __name__ == "__main__":
    asyncio.run(run())
