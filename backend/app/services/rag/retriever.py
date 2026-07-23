from typing import Sequence
from app.domain.rag import KnowledgeRetriever, EmbeddingProvider, VectorStore, KnowledgeChunk, RetrievalResult, Metadata


class DefaultKnowledgeRetriever(KnowledgeRetriever):
    """
    Production-ready implementation of KnowledgeRetriever that coordinates
    an EmbeddingProvider and a VectorStore to ingest and retrieve documents.
    """

    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter_metadata: Metadata | None = None,
    ) -> RetrievalResult:
        if not query or not query.strip():
            raise ValueError("Query string must be non-empty.")

        # 1. Generate query embedding
        query_vector = await self.embedding_provider.aembed(query)

        # 2. Retrieve similar chunks
        chunks = await self.vector_store.query(
            query_embedding=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            filter_metadata=filter_metadata
        )

        return RetrievalResult(
            chunks=tuple(chunks),
            query=query
        )

    async def ingest(self, chunks: Sequence[KnowledgeChunk]) -> None:
        if not chunks:
            return

        # 1. Generate embeddings in batch
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_provider.aembed_batch(texts)

        # 2. Store in vector database
        await self.vector_store.upsert(chunks, embeddings)
