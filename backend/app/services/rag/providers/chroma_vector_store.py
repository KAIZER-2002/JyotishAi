import asyncio
from typing import Sequence
import chromadb
from app.domain.rag import VectorStore, KnowledgeChunk, RetrievedChunk, Embedding, Metadata, VectorStoreException
from app.core.config import settings


class ChromaVectorStore(VectorStore):
    """
    Chroma-backed implementation of the VectorStore interface.
    """

    def __init__(self, persist_directory: str = "chroma_db", collection_name: str = "jyotish_knowledge") -> None:
        try:
            if settings.CHROMA_HOST and settings.CHROMA_PORT:
                self._client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT
                )
            else:
                self._client = chromadb.PersistentClient(
                    path=persist_directory
                )
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._collection_name = collection_name
        except Exception as e:
            raise VectorStoreException(f"Failed to initialize Chroma client: {e}") from e

    @property
    def store_name(self) -> str:
        return self._collection_name

    async def upsert(self, chunks: Sequence[KnowledgeChunk], embeddings: Sequence[Embedding]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return

        def _sync_upsert():
            ids = [chunk.id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            
            # Convert arbitrary Metadata to chroma-compatible metadata (strings, ints, floats, bools only)
            metadatas = []
            for chunk in chunks:
                meta = {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                }
                # Add extra metadata elements that are of basic types
                for k, v in chunk.metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        meta[k] = v
                metadatas.append(meta)

            self._collection.upsert(
                ids=ids,
                embeddings=[list(emb) for emb in embeddings],
                documents=documents,
                metadatas=metadatas
            )

        try:
            await asyncio.to_thread(_sync_upsert)
        except Exception as e:
            raise VectorStoreException(f"Chroma upsert failed: {e}") from e

    async def query(
        self,
        query_embedding: Embedding,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter_metadata: Metadata | None = None,
    ) -> list[RetrievedChunk]:
        
        def _sync_query():
            where = None
            if filter_metadata:
                clean_filters = {
                    k: v for k, v in filter_metadata.items()
                    if isinstance(v, (str, int, float, bool))
                }
                if len(clean_filters) == 1:
                    k, v = list(clean_filters.items())[0]
                    where = {k: v}
                elif len(clean_filters) > 1:
                    where = {"$and": [{k: v} for k, v in clean_filters.items()]}

            return self._collection.query(
                query_embeddings=[list(query_embedding)],
                n_results=top_k,
                where=where
            )

        try:
            raw = await asyncio.to_thread(_sync_query)
            retrieved = []
            if not raw or not raw.get("ids") or not raw["ids"][0]:
                return retrieved

            ids = raw["ids"][0]
            documents = raw["documents"][0] if raw.get("documents") else []
            metadatas = raw["metadatas"][0] if raw.get("metadatas") else []
            distances = raw["distances"][0] if raw.get("distances") else []

            for idx in range(len(ids)):
                cid = ids[idx]
                content = documents[idx] if idx < len(documents) else ""
                meta = metadatas[idx] if idx < len(metadatas) else {}
                
                dist = distances[idx] if idx < len(distances) else 0.0
                # Cosine distance to similarity conversion
                score = 1.0 - dist
                score = max(0.0, min(1.0, score))

                if score < score_threshold:
                    continue

                chunk = KnowledgeChunk(
                    id=cid,
                    document_id=meta.get("document_id", ""),
                    content=content,
                    chunk_index=int(meta.get("chunk_index", 0)),
                    start_char=int(meta.get("start_char", -1)),
                    end_char=int(meta.get("end_char", -1)),
                    metadata={k: v for k, v in meta.items() if k not in ("document_id", "chunk_index", "start_char", "end_char")}
                )
                retrieved.append(RetrievedChunk(chunk=chunk, score=score))

            return sorted(retrieved, key=lambda x: x.score, reverse=True)
        except Exception as e:
            raise VectorStoreException(f"Chroma query failed: {e}") from e

    async def delete(self, chunk_ids: Sequence[str]) -> None:
        if not chunk_ids:
            return
        
        def _sync_delete():
            self._collection.delete(ids=list(chunk_ids))

        try:
            await asyncio.to_thread(_sync_delete)
        except Exception as e:
            raise VectorStoreException(f"Chroma delete failed: {e}") from e

    async def exists(self, chunk_id: str) -> bool:
        def _sync_exists():
            res = self._collection.get(ids=[chunk_id])
            return bool(res and res.get("ids"))

        try:
            return await asyncio.to_thread(_sync_exists)
        except Exception as e:
            raise VectorStoreException(f"Chroma exists check failed: {e}") from e

    async def count(self) -> int:
        try:
            return await asyncio.to_thread(self._collection.count)
        except Exception as e:
            raise VectorStoreException(f"Chroma count failed: {e}") from e
