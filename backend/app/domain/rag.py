"""
RAG (Retrieval-Augmented Generation) abstraction layer.

Provider-agnostic domain models and interfaces for knowledge retrieval.
No network calls, no Qdrant, no Gemini, no FastAPI, no SQLAlchemy.

Concrete implementations (Qdrant, Chroma, Pinecone, etc.) subclass the
abstract providers defined here and are kept outside this module.

Public surface
--------------
Value objects (frozen dataclasses):
    KnowledgeDocument   — a raw source document with metadata
    KnowledgeChunk      — a text segment derived from a document
    RetrievedChunk      — a KnowledgeChunk annotated with a similarity score
    RetrievalResult     — the ordered collection returned from a retrieval call

Interfaces (ABCs):
    EmbeddingProvider   — turns text into dense float vectors
    VectorStore         — stores and queries vector-indexed chunks
    KnowledgeRetriever  — high-level retriever combining the two above
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Sequence


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

Embedding = list[float]
"""Dense float vector produced by an EmbeddingProvider."""

class EmbeddingException(Exception):
    """Exception raised when an embedding operation fails."""
    pass


class VectorStoreException(Exception):
    """Exception raised when a vector store operation fails."""
    pass


@dataclass(frozen=True)
class EmbeddingVector:
    """
    A domain model wrapping a dense float vector embedding.
    """
    values: list[float]

    @property
    def dimension(self) -> int:
        """Return the dimension of the embedding vector."""
        return len(self.values)


Metadata = dict[str, Any]
"""Arbitrary key-value metadata attached to documents or chunks."""


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class KnowledgeDocument:
    """
    A raw source document that has been ingested into the knowledge base.

    Attributes
    ----------
    id:
        Stable, unique identifier for this document (e.g. a UUID string or
        a canonical URL slug).  Set by the ingestion pipeline.
    content:
        Full raw text of the document before chunking.
    source:
        Human-readable origin of the document (e.g. a file path, URL, or
        database table identifier).  Used for provenance tracking.
    metadata:
        Arbitrary provider-agnostic key/value pairs (e.g. author, date,
        topic tags).  Stored alongside the document for filtering.
    """

    id: str
    content: str
    source: str = ""
    metadata: Metadata = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def char_count(self) -> int:
        """Number of characters in the raw content."""
        return len(self.content)

    @property
    def word_count(self) -> int:
        """Approximate word count of the raw content."""
        return len(self.content.split())

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary (e.g. for logging or REST responses)."""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class KnowledgeChunk:
    """
    A contiguous segment of text derived from a KnowledgeDocument.

    Chunking strategy (fixed-size, semantic, etc.) is the responsibility of
    the ingestion pipeline; this model simply records the result.

    Attributes
    ----------
    id:
        Stable, unique identifier for this chunk.  Typically derived from
        the document id and the chunk index (e.g. ``"doc-abc_chunk-3"``).
    document_id:
        The ``KnowledgeDocument.id`` this chunk was split from.
    content:
        The text content of this chunk.
    chunk_index:
        Zero-based position of this chunk within its parent document.
    start_char:
        Character offset (inclusive) within the original document where this
        chunk begins.  -1 if unknown.
    end_char:
        Character offset (exclusive) within the original document where this
        chunk ends.  -1 if unknown.
    metadata:
        Additional key/value pairs (inherits from the parent document and
        may be enriched by the chunking pipeline).
    """

    id: str
    document_id: str
    content: str
    chunk_index: int = 0
    start_char: int = -1
    end_char: int = -1
    metadata: Metadata = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def char_count(self) -> int:
        """Number of characters in this chunk."""
        return len(self.content)

    @property
    def has_position(self) -> bool:
        """True when the chunk carries valid start/end character offsets."""
        return self.start_char >= 0 and self.end_char >= 0

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RetrievedChunk:
    """
    A KnowledgeChunk annotated with a similarity score from a vector search.

    Attributes
    ----------
    chunk:
        The underlying knowledge chunk.
    score:
        Provider-normalised similarity score in the range [0.0, 1.0].
        Higher is more relevant.  The exact metric (cosine, dot-product,
        Euclidean) is determined by the VectorStore implementation.
    """

    chunk: KnowledgeChunk
    score: float

    # ------------------------------------------------------------------
    # Convenience proxies
    # ------------------------------------------------------------------

    @property
    def id(self) -> str:
        """Shortcut to the underlying chunk id."""
        return self.chunk.id

    @property
    def document_id(self) -> str:
        """Shortcut to the underlying document id."""
        return self.chunk.document_id

    @property
    def content(self) -> str:
        """Shortcut to the underlying chunk content."""
        return self.chunk.content

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
        }


@dataclass(frozen=True)
class RetrievalResult:
    """
    The ordered collection of retrieved chunks returned by a KnowledgeRetriever.

    Attributes
    ----------
    chunks:
        Retrieved chunks in descending relevance order (highest score first).
    query:
        The original query string that produced this result set.
    total_candidates:
        Number of candidates considered before top-k selection.
        0 if the backend did not report this value.
    """

    chunks: tuple[RetrievedChunk, ...]
    query: str
    total_candidates: int = 0

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def is_empty(self) -> bool:
        """True when no chunks were retrieved."""
        return len(self.chunks) == 0

    @property
    def top_chunk(self) -> RetrievedChunk | None:
        """The highest-scoring chunk, or None when the result is empty."""
        return self.chunks[0] if self.chunks else None

    @property
    def scores(self) -> tuple[float, ...]:
        """All similarity scores in the same order as ``chunks``."""
        return tuple(c.score for c in self.chunks)

    @property
    def texts(self) -> tuple[str, ...]:
        """All chunk texts in the same order as ``chunks``."""
        return tuple(c.content for c in self.chunks)

    def above_threshold(self, threshold: float) -> tuple[RetrievedChunk, ...]:
        """Return only the chunks whose score meets or exceeds *threshold*."""
        return tuple(c for c in self.chunks if c.score >= threshold)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "query": self.query,
            "total_candidates": self.total_candidates,
            "chunks": [c.to_dict() for c in self.chunks],
        }


# ---------------------------------------------------------------------------
# Provider interfaces
# ---------------------------------------------------------------------------


class EmbeddingProvider(ABC):
    """
    Abstract base class for text embedding providers.

    Concrete implementations (Gemini, OpenAI, local sentence-transformers,
    etc.) must subclass EmbeddingProvider and implement the two abstract
    methods below.  No provider-specific types leak across this boundary.

    All embeddings are returned as ``list[float]`` so callers can remain
    independent of any provider SDK.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Short stable identifier for this provider (e.g. ``'gemini'``, ``'openai'``)."""

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Dimensionality of the vectors produced by this provider."""

    @abstractmethod
    def embed(self, text: str) -> Embedding:
        """
        Produce a dense vector representation of a single text string.

        Parameters
        ----------
        text:
            The input string to embed.  Must be non-empty.

        Returns
        -------
        Embedding
            A ``list[float]`` of length ``embedding_dimension``.

        Raises
        ------
        EmbeddingException
            If the provider fails to produce an embedding.
        """

    @abstractmethod
    async def aembed(self, text: str) -> Embedding:
        """
        Asynchronous variant of :meth:`embed`.

        Parameters
        ----------
        text:
            The input string to embed.  Must be non-empty.

        Returns
        -------
        Embedding
            A ``list[float]`` of length ``embedding_dimension``.

        Raises
        ------
        EmbeddingException
            If the provider fails to produce an embedding.
        """

    @abstractmethod
    def embed_batch(self, texts: Sequence[str]) -> list[Embedding]:
        """
        Embed multiple texts in a single provider call (where supported).

        Implementations MAY fall back to calling :meth:`embed` in a loop if
        the underlying provider does not support batching natively.

        Parameters
        ----------
        texts:
            A sequence of non-empty strings to embed.

        Returns
        -------
        list[Embedding]
            One embedding per input string, in the same order.

        Raises
        ------
        EmbeddingException
            If the provider fails for any text in the batch.
        """

    @abstractmethod
    async def aembed_batch(self, texts: Sequence[str]) -> list[Embedding]:
        """
        Asynchronous variant of :meth:`embed_batch`.

        Parameters
        ----------
        texts:
            A sequence of non-empty strings to embed.

        Returns
        -------
        list[Embedding]
            One embedding per input string, in the same order.

        Raises
        ------
        EmbeddingException
            If the provider fails for any text in the batch.
        """


class VectorStore(ABC):
    """
    Abstract base class for vector storage and nearest-neighbour retrieval.

    Concrete implementations (Qdrant, Chroma, Pinecone, FAISS, etc.) must
    subclass VectorStore and implement the abstract methods below.

    Design constraints
    ------------------
    * All public methods deal only in domain types (KnowledgeChunk,
      RetrievedChunk, Embedding).
    * No SDK-specific types, HTTP clients, or connection objects are part of
      the interface.
    * Implementations are responsible for their own connection management.
    """

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Human-readable identifier for this store instance (e.g. collection name)."""

    @abstractmethod
    async def upsert(self, chunks: Sequence[KnowledgeChunk], embeddings: Sequence[Embedding]) -> None:
        """
        Insert or update chunks together with their pre-computed embeddings.

        Parameters
        ----------
        chunks:
            The knowledge chunks to store.  ``len(chunks)`` must equal
            ``len(embeddings)``.
        embeddings:
            Pre-computed dense vectors, one per chunk.

        Raises
        ------
        VectorStoreException
            If the backend rejects the upsert.
        ValueError
            If ``len(chunks) != len(embeddings)``.
        """

    @abstractmethod
    async def query(
        self,
        query_embedding: Embedding,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter_metadata: Metadata | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve the *top_k* most similar chunks for a query embedding.

        Parameters
        ----------
        query_embedding:
            The dense query vector produced by an EmbeddingProvider.
        top_k:
            Maximum number of chunks to return.
        score_threshold:
            Minimum similarity score a chunk must meet to be included.
            Defaults to ``0.0`` (no filtering).
        filter_metadata:
            Optional key/value pairs used to pre-filter the search space
            (e.g. ``{"source": "rig_veda"}``).  Semantics are
            store-specific; pass ``None`` for no filtering.

        Returns
        -------
        list[RetrievedChunk]
            Chunks in descending similarity order.

        Raises
        ------
        VectorStoreException
            If the backend query fails.
        """

    @abstractmethod
    async def delete(self, chunk_ids: Sequence[str]) -> None:
        """
        Remove chunks by their ids.

        Parameters
        ----------
        chunk_ids:
            Ids of the chunks to delete.  Unknown ids are silently ignored.

        Raises
        ------
        VectorStoreException
            If the backend operation fails.
        """

    @abstractmethod
    async def exists(self, chunk_id: str) -> bool:
        """
        Check whether a chunk with the given id is stored.

        Parameters
        ----------
        chunk_id:
            The chunk id to look up.

        Returns
        -------
        bool
            ``True`` if the chunk exists, ``False`` otherwise.

        Raises
        ------
        VectorStoreException
            If the backend lookup fails.
        """

    @abstractmethod
    async def count(self) -> int:
        """
        Return the total number of chunks currently stored.

        Raises
        ------
        VectorStoreException
            If the backend count fails.
        """


class KnowledgeRetriever(ABC):
    """
    High-level, provider-agnostic retriever interface.

    A KnowledgeRetriever orchestrates an EmbeddingProvider and a VectorStore
    to turn a raw text query into a RetrievalResult.  It is the primary entry
    point for RAG pipelines and must remain independent of any concrete
    embedding or storage technology.

    Implementations are free to add re-ranking, query expansion, hybrid
    search, or other retrieval strategies internally without changing this
    interface.
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter_metadata: Metadata | None = None,
    ) -> RetrievalResult:
        """
        Embed *query* and fetch the most relevant knowledge chunks.

        Parameters
        ----------
        query:
            The natural-language query string.  Must be non-empty.
        top_k:
            Maximum number of chunks to include in the result.
        score_threshold:
            Minimum similarity score for a chunk to be returned.
        filter_metadata:
            Optional key/value metadata filter forwarded to the VectorStore.

        Returns
        -------
        RetrievalResult
            Ordered collection of retrieved chunks with scores.

        Raises
        ------
        ValueError
            If *query* is empty.
        EmbeddingException
            If the embedding provider fails.
        VectorStoreException
            If the vector store query fails.
        """

    @abstractmethod
    async def ingest(
        self,
        chunks: Sequence[KnowledgeChunk],
    ) -> None:
        """
        Embed and store a batch of knowledge chunks.

        This method is intentionally minimal — chunking strategy and document
        parsing are concerns of the ingestion pipeline, not the retriever.

        Parameters
        ----------
        chunks:
            Pre-chunked knowledge pieces to embed and persist.

        Raises
        ------
        EmbeddingException
            If embedding any chunk fails.
        VectorStoreException
            If upserting to the store fails.
        """
