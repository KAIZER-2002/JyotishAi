"""
Unit tests for app.domain.rag — the provider-agnostic RAG abstraction layer.

Coverage:
  - KnowledgeDocument: immutability, equality, helpers, serialisation
  - KnowledgeChunk: immutability, equality, helpers, serialisation
  - RetrievedChunk: immutability, equality, proxy properties, serialisation
  - RetrievalResult: immutability, helpers, filtering, serialisation
  - EmbeddingProvider: ABC cannot be instantiated; abstract contract enforced
  - VectorStore: ABC cannot be instantiated; abstract contract enforced
  - KnowledgeRetriever: ABC cannot be instantiated; abstract contract enforced
  - Concrete minimal stubs satisfy the full abstract contracts
"""

from __future__ import annotations

import pytest
from dataclasses import FrozenInstanceError
from typing import Sequence
from unittest.mock import AsyncMock

from app.domain.rag import (
    Embedding,
    Metadata,
    KnowledgeDocument,
    KnowledgeChunk,
    RetrievedChunk,
    RetrievalResult,
    EmbeddingProvider,
    VectorStore,
    KnowledgeRetriever,
)


# ---------------------------------------------------------------------------
# Helpers / minimal concrete implementations
# ---------------------------------------------------------------------------


class _StubEmbeddingProvider(EmbeddingProvider):
    """Minimal concrete EmbeddingProvider used in contract tests."""

    @property
    def provider_name(self) -> str:
        return "stub"

    @property
    def embedding_dimension(self) -> int:
        return 4

    def embed(self, text: str) -> Embedding:
        return [0.1, 0.2, 0.3, 0.4]

    async def aembed(self, text: str) -> Embedding:
        return self.embed(text)

    def embed_batch(self, texts: Sequence[str]) -> list[Embedding]:
        return [self.embed(t) for t in texts]

    async def aembed_batch(self, texts: Sequence[str]) -> list[Embedding]:
        return self.embed_batch(texts)


class _StubVectorStore(VectorStore):
    """Minimal concrete VectorStore backed by an in-memory list."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[KnowledgeChunk, Embedding]] = {}

    @property
    def store_name(self) -> str:
        return "stub-store"

    async def upsert(self, chunks: Sequence[KnowledgeChunk], embeddings: Sequence[Embedding]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        for chunk, emb in zip(chunks, embeddings):
            self._store[chunk.id] = (chunk, emb)

    async def query(
        self,
        query_embedding: Embedding,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter_metadata: Metadata | None = None,
    ) -> list[RetrievedChunk]:
        results = [
            RetrievedChunk(chunk=c, score=0.9)
            for c, _ in self._store.values()
        ]
        return sorted(results, key=lambda r: r.score, reverse=True)[:top_k]

    async def delete(self, chunk_ids: Sequence[str]) -> None:
        for cid in chunk_ids:
            self._store.pop(cid, None)

    async def exists(self, chunk_id: str) -> bool:
        return chunk_id in self._store

    async def count(self) -> int:
        return len(self._store)


class _StubKnowledgeRetriever(KnowledgeRetriever):
    """Minimal concrete KnowledgeRetriever."""

    def __init__(self, ep: EmbeddingProvider, vs: VectorStore) -> None:
        self._ep = ep
        self._vs = vs

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter_metadata: Metadata | None = None,
    ) -> RetrievalResult:
        if not query.strip():
            raise ValueError("query cannot be empty")
        emb = await self._ep.aembed(query)
        raw = await self._vs.query(emb, top_k=top_k, score_threshold=score_threshold)
        filtered = [c for c in raw if c.score >= score_threshold]
        return RetrievalResult(
            chunks=tuple(filtered),
            query=query,
            total_candidates=len(raw),
        )

    async def ingest(self, chunks: Sequence[KnowledgeChunk]) -> None:
        embeddings = await self._ep.aembed_batch([c.content for c in chunks])
        await self._vs.upsert(chunks, embeddings)


def _make_chunk(
    chunk_id: str = "chunk-1",
    document_id: str = "doc-1",
    content: str = "Some chunk text.",
    chunk_index: int = 0,
    start_char: int = 0,
    end_char: int = 16,
    metadata: Metadata | None = None,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=chunk_id,
        document_id=document_id,
        content=content,
        chunk_index=chunk_index,
        start_char=start_char,
        end_char=end_char,
        metadata=metadata or {},
    )


def _make_doc(
    doc_id: str = "doc-1",
    content: str = "Full document text.",
    source: str = "test_source",
    metadata: Metadata | None = None,
) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=doc_id,
        content=content,
        source=source,
        metadata=metadata or {},
    )


# ===========================================================================
# KnowledgeDocument tests
# ===========================================================================


class TestKnowledgeDocument:
    def test_basic_construction(self):
        doc = _make_doc()
        assert doc.id == "doc-1"
        assert doc.content == "Full document text."
        assert doc.source == "test_source"

    def test_default_source_and_metadata(self):
        doc = KnowledgeDocument(id="x", content="hello")
        assert doc.source == ""
        assert doc.metadata == {}

    def test_immutable_top_level_fields(self):
        doc = _make_doc()
        with pytest.raises(FrozenInstanceError):
            doc.id = "new-id"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            doc.content = "new content"  # type: ignore[misc]

    def test_immutable_source(self):
        doc = _make_doc()
        with pytest.raises(FrozenInstanceError):
            doc.source = "other"  # type: ignore[misc]

    def test_equality_same_values(self):
        a = _make_doc()
        b = _make_doc()
        assert a == b

    def test_equality_different_id(self):
        a = _make_doc(doc_id="doc-1")
        b = _make_doc(doc_id="doc-2")
        assert a != b

    def test_equality_different_content(self):
        a = _make_doc(content="AAA")
        b = _make_doc(content="BBB")
        assert a != b

    def test_char_count(self):
        doc = _make_doc(content="hello world")
        assert doc.char_count == 11

    def test_word_count(self):
        doc = _make_doc(content="one two three")
        assert doc.word_count == 3

    def test_word_count_empty(self):
        doc = _make_doc(content="")
        assert doc.word_count == 0

    def test_to_dict_structure(self):
        doc = _make_doc(metadata={"author": "Vyasa"})
        d = doc.to_dict()
        assert d["id"] == "doc-1"
        assert d["content"] == "Full document text."
        assert d["source"] == "test_source"
        assert d["metadata"] == {"author": "Vyasa"}

    def test_to_dict_is_copy(self):
        """Mutating the returned dict must not affect the frozen dataclass."""
        doc = _make_doc(metadata={"k": "v"})
        d = doc.to_dict()
        d["metadata"]["k"] = "mutated"
        assert doc.metadata["k"] == "v"


    def test_metadata_with_nested_values(self):
        doc = KnowledgeDocument(
            id="doc-1",
            content="text",
            metadata={"tags": ["yoga", "vedanta"], "chapter": 3},
        )
        assert doc.metadata["tags"] == ["yoga", "vedanta"]
        assert doc.metadata["chapter"] == 3


# ===========================================================================
# KnowledgeChunk tests
# ===========================================================================


class TestKnowledgeChunk:
    def test_basic_construction(self):
        chunk = _make_chunk()
        assert chunk.id == "chunk-1"
        assert chunk.document_id == "doc-1"
        assert chunk.content == "Some chunk text."
        assert chunk.chunk_index == 0

    def test_default_optional_fields(self):
        chunk = KnowledgeChunk(id="c", document_id="d", content="text")
        assert chunk.chunk_index == 0
        assert chunk.start_char == -1
        assert chunk.end_char == -1
        assert chunk.metadata == {}

    def test_immutable_id(self):
        chunk = _make_chunk()
        with pytest.raises(FrozenInstanceError):
            chunk.id = "new"  # type: ignore[misc]

    def test_immutable_content(self):
        chunk = _make_chunk()
        with pytest.raises(FrozenInstanceError):
            chunk.content = "new"  # type: ignore[misc]

    def test_immutable_chunk_index(self):
        chunk = _make_chunk()
        with pytest.raises(FrozenInstanceError):
            chunk.chunk_index = 99  # type: ignore[misc]

    def test_equality_same_values(self):
        a = _make_chunk()
        b = _make_chunk()
        assert a == b

    def test_equality_different_content(self):
        a = _make_chunk(content="A")
        b = _make_chunk(content="B")
        assert a != b

    def test_equality_different_index(self):
        a = _make_chunk(chunk_index=0)
        b = _make_chunk(chunk_index=1)
        assert a != b

    def test_char_count(self):
        chunk = _make_chunk(content="hello world")
        assert chunk.char_count == 11

    def test_has_position_true(self):
        chunk = _make_chunk(start_char=0, end_char=10)
        assert chunk.has_position is True

    def test_has_position_false_unknown(self):
        chunk = KnowledgeChunk(id="c", document_id="d", content="text")
        assert chunk.has_position is False

    def test_has_position_false_negative_start(self):
        chunk = KnowledgeChunk(id="c", document_id="d", content="text", start_char=-1, end_char=10)
        assert chunk.has_position is False

    def test_to_dict_structure(self):
        chunk = _make_chunk(metadata={"source": "Rig Veda 1.1"})
        d = chunk.to_dict()
        assert d["id"] == "chunk-1"
        assert d["document_id"] == "doc-1"
        assert d["content"] == "Some chunk text."
        assert d["chunk_index"] == 0
        assert d["start_char"] == 0
        assert d["end_char"] == 16
        assert d["metadata"] == {"source": "Rig Veda 1.1"}

    def test_to_dict_metadata_is_copy(self):
        chunk = _make_chunk(metadata={"k": "v"})
        d = chunk.to_dict()
        d["metadata"]["k"] = "mutated"
        assert chunk.metadata["k"] == "v"



# ===========================================================================
# RetrievedChunk tests
# ===========================================================================


class TestRetrievedChunk:
    def _make(self, score: float = 0.85) -> RetrievedChunk:
        chunk = _make_chunk()
        return RetrievedChunk(chunk=chunk, score=score)

    def test_basic_construction(self):
        rc = self._make()
        assert rc.score == 0.85
        assert rc.chunk.id == "chunk-1"

    def test_immutable_score(self):
        rc = self._make()
        with pytest.raises(FrozenInstanceError):
            rc.score = 0.5  # type: ignore[misc]

    def test_immutable_chunk(self):
        rc = self._make()
        with pytest.raises(FrozenInstanceError):
            rc.chunk = _make_chunk(chunk_id="other")  # type: ignore[misc]

    def test_equality_same(self):
        a = self._make(0.9)
        b = self._make(0.9)
        assert a == b

    def test_equality_different_score(self):
        a = self._make(0.9)
        b = self._make(0.8)
        assert a != b

    def test_proxy_id(self):
        rc = self._make()
        assert rc.id == "chunk-1"

    def test_proxy_document_id(self):
        rc = self._make()
        assert rc.document_id == "doc-1"

    def test_proxy_content(self):
        rc = self._make()
        assert rc.content == "Some chunk text."

    def test_to_dict_structure(self):
        rc = self._make(0.77)
        d = rc.to_dict()
        assert d["score"] == 0.77
        assert "chunk" in d
        assert d["chunk"]["id"] == "chunk-1"



# ===========================================================================
# RetrievalResult tests
# ===========================================================================


class TestRetrievalResult:
    def _make_result(
        self,
        n_chunks: int = 3,
        scores: list[float] | None = None,
        query: str = "test query",
    ) -> RetrievalResult:
        if scores is None:
            scores = [0.9 - i * 0.1 for i in range(n_chunks)]
        chunks = tuple(
            RetrievedChunk(
                chunk=_make_chunk(
                    chunk_id=f"chunk-{i}",
                    content=f"Text {i}.",
                    chunk_index=i,
                ),
                score=scores[i],
            )
            for i in range(n_chunks)
        )
        return RetrievalResult(chunks=chunks, query=query, total_candidates=10)

    def test_basic_construction(self):
        result = self._make_result()
        assert result.query == "test query"
        assert len(result.chunks) == 3
        assert result.total_candidates == 10

    def test_immutable_chunks(self):
        result = self._make_result()
        with pytest.raises(FrozenInstanceError):
            result.chunks = ()  # type: ignore[misc]

    def test_immutable_query(self):
        result = self._make_result()
        with pytest.raises(FrozenInstanceError):
            result.query = "other"  # type: ignore[misc]

    def test_is_empty_false(self):
        result = self._make_result(n_chunks=2)
        assert result.is_empty is False

    def test_is_empty_true(self):
        result = RetrievalResult(chunks=(), query="q")
        assert result.is_empty is True

    def test_top_chunk_non_empty(self):
        result = self._make_result(n_chunks=3, scores=[0.9, 0.8, 0.7])
        assert result.top_chunk is not None
        assert result.top_chunk.score == 0.9

    def test_top_chunk_empty_result(self):
        result = RetrievalResult(chunks=(), query="q")
        assert result.top_chunk is None

    def test_scores_property(self):
        result = self._make_result(n_chunks=3, scores=[0.9, 0.8, 0.7])
        assert result.scores == (0.9, 0.8, 0.7)

    def test_texts_property(self):
        result = self._make_result(n_chunks=2)
        assert result.texts == ("Text 0.", "Text 1.")

    def test_above_threshold_all_pass(self):
        result = self._make_result(n_chunks=3, scores=[0.9, 0.8, 0.7])
        above = result.above_threshold(0.5)
        assert len(above) == 3

    def test_above_threshold_partial(self):
        result = self._make_result(n_chunks=3, scores=[0.9, 0.6, 0.3])
        above = result.above_threshold(0.7)
        assert len(above) == 1
        assert above[0].score == 0.9

    def test_above_threshold_none_pass(self):
        result = self._make_result(n_chunks=3, scores=[0.2, 0.1, 0.05])
        above = result.above_threshold(0.5)
        assert len(above) == 0

    def test_above_threshold_returns_tuple(self):
        result = self._make_result()
        above = result.above_threshold(0.0)
        assert isinstance(above, tuple)

    def test_to_dict_structure(self):
        result = self._make_result(n_chunks=2, query="my query")
        d = result.to_dict()
        assert d["query"] == "my query"
        assert d["total_candidates"] == 10
        assert len(d["chunks"]) == 2
        assert "score" in d["chunks"][0]
        assert "chunk" in d["chunks"][0]

    def test_default_total_candidates(self):
        result = RetrievalResult(chunks=(), query="q")
        assert result.total_candidates == 0



# ===========================================================================
# EmbeddingProvider ABC contract tests
# ===========================================================================


class TestEmbeddingProviderABC:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            EmbeddingProvider()  # type: ignore[abstract]

    def test_concrete_stub_satisfies_interface(self):
        ep = _StubEmbeddingProvider()
        assert isinstance(ep, EmbeddingProvider)

    def test_provider_name(self):
        ep = _StubEmbeddingProvider()
        assert ep.provider_name == "stub"

    def test_embedding_dimension(self):
        ep = _StubEmbeddingProvider()
        assert ep.embedding_dimension == 4

    def test_embed_returns_list_of_float(self):
        ep = _StubEmbeddingProvider()
        result = ep.embed("hello")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)
        assert len(result) == ep.embedding_dimension

    @pytest.mark.asyncio
    async def test_aembed_returns_list_of_float(self):
        ep = _StubEmbeddingProvider()
        result = await ep.aembed("hello")
        assert isinstance(result, list)
        assert len(result) == ep.embedding_dimension

    def test_embed_batch_returns_multiple_embeddings(self):
        ep = _StubEmbeddingProvider()
        texts = ["a", "b", "c"]
        results = ep.embed_batch(texts)
        assert len(results) == 3
        assert all(len(r) == ep.embedding_dimension for r in results)

    @pytest.mark.asyncio
    async def test_aembed_batch_returns_multiple_embeddings(self):
        ep = _StubEmbeddingProvider()
        texts = ["x", "y"]
        results = await ep.aembed_batch(texts)
        assert len(results) == 2

    def test_missing_abstract_method_raises_type_error(self):
        """A class missing any abstract method cannot be instantiated."""

        class _Incomplete(EmbeddingProvider):
            @property
            def provider_name(self) -> str:
                return "x"

            @property
            def embedding_dimension(self) -> int:
                return 1

            def embed(self, text: str) -> Embedding:
                return [0.0]

            async def aembed(self, text: str) -> Embedding:
                return [0.0]

            def embed_batch(self, texts) -> list[Embedding]:
                return [[0.0] for _ in texts]

            # aembed_batch deliberately omitted

        with pytest.raises(TypeError):
            _Incomplete()  # type: ignore[abstract]


# ===========================================================================
# VectorStore ABC contract tests
# ===========================================================================


class TestVectorStoreABC:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            VectorStore()  # type: ignore[abstract]

    def test_concrete_stub_satisfies_interface(self):
        vs = _StubVectorStore()
        assert isinstance(vs, VectorStore)

    def test_store_name(self):
        vs = _StubVectorStore()
        assert vs.store_name == "stub-store"

    @pytest.mark.asyncio
    async def test_upsert_and_count(self):
        vs = _StubVectorStore()
        chunk = _make_chunk()
        await vs.upsert([chunk], [[0.1, 0.2, 0.3, 0.4]])
        assert await vs.count() == 1

    @pytest.mark.asyncio
    async def test_upsert_multiple(self):
        vs = _StubVectorStore()
        chunks = [_make_chunk(chunk_id=f"c-{i}") for i in range(3)]
        embeddings = [[float(i)] * 4 for i in range(3)]
        await vs.upsert(chunks, embeddings)
        assert await vs.count() == 3

    @pytest.mark.asyncio
    async def test_upsert_length_mismatch_raises(self):
        vs = _StubVectorStore()
        chunks = [_make_chunk(chunk_id="c1"), _make_chunk(chunk_id="c2")]
        embeddings = [[0.1, 0.2]]  # only 1 embedding for 2 chunks
        with pytest.raises(ValueError):
            await vs.upsert(chunks, embeddings)

    @pytest.mark.asyncio
    async def test_query_returns_retrieved_chunks(self):
        vs = _StubVectorStore()
        chunk = _make_chunk(chunk_id="c1", content="Jupiter in 1st house")
        await vs.upsert([chunk], [[0.5, 0.5, 0.5, 0.5]])
        results = await vs.query(query_embedding=[0.5, 0.5, 0.5, 0.5])
        assert len(results) == 1
        assert isinstance(results[0], RetrievedChunk)
        assert results[0].chunk.id == "c1"

    @pytest.mark.asyncio
    async def test_query_top_k_limits_results(self):
        vs = _StubVectorStore()
        for i in range(10):
            await vs.upsert(
                [_make_chunk(chunk_id=f"c-{i}", content=f"Text {i}")],
                [[float(i)] * 4],
            )
        results = await vs.query(query_embedding=[0.5] * 4, top_k=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_exists_true(self):
        vs = _StubVectorStore()
        chunk = _make_chunk(chunk_id="x")
        await vs.upsert([chunk], [[0.1, 0.2, 0.3, 0.4]])
        assert await vs.exists("x") is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        vs = _StubVectorStore()
        assert await vs.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_delete_removes_chunk(self):
        vs = _StubVectorStore()
        chunk = _make_chunk(chunk_id="del-me")
        await vs.upsert([chunk], [[0.1, 0.2, 0.3, 0.4]])
        assert await vs.exists("del-me") is True
        await vs.delete(["del-me"])
        assert await vs.exists("del-me") is False
        assert await vs.count() == 0

    @pytest.mark.asyncio
    async def test_delete_unknown_id_is_noop(self):
        vs = _StubVectorStore()
        await vs.delete(["ghost"])  # should not raise

    @pytest.mark.asyncio
    async def test_count_empty_store(self):
        vs = _StubVectorStore()
        assert await vs.count() == 0

    def test_missing_abstract_method_raises_type_error(self):
        class _Incomplete(VectorStore):
            @property
            def store_name(self) -> str:
                return "x"

            async def upsert(self, chunks, embeddings) -> None:
                pass

            async def query(self, query_embedding, top_k=5, score_threshold=0.0, filter_metadata=None):
                return []

            async def delete(self, chunk_ids) -> None:
                pass

            async def exists(self, chunk_id) -> bool:
                return False

            # count deliberately omitted

        with pytest.raises(TypeError):
            _Incomplete()  # type: ignore[abstract]


# ===========================================================================
# KnowledgeRetriever ABC contract tests
# ===========================================================================


class TestKnowledgeRetrieverABC:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            KnowledgeRetriever()  # type: ignore[abstract]

    def test_concrete_stub_satisfies_interface(self):
        ep = _StubEmbeddingProvider()
        vs = _StubVectorStore()
        retriever = _StubKnowledgeRetriever(ep, vs)
        assert isinstance(retriever, KnowledgeRetriever)

    @pytest.mark.asyncio
    async def test_ingest_and_retrieve_roundtrip(self):
        ep = _StubEmbeddingProvider()
        vs = _StubVectorStore()
        retriever = _StubKnowledgeRetriever(ep, vs)

        chunks = [
            _make_chunk(chunk_id="c1", content="Gaja Kesari Yoga — Jupiter and Moon."),
            _make_chunk(chunk_id="c2", content="Pancha Mahapurusha — Mars in own sign."),
        ]
        await retriever.ingest(chunks)

        result = await retriever.retrieve("Jupiter yoga", top_k=2)
        assert isinstance(result, RetrievalResult)
        assert not result.is_empty
        assert len(result.chunks) <= 2

    @pytest.mark.asyncio
    async def test_retrieve_empty_query_raises(self):
        ep = _StubEmbeddingProvider()
        vs = _StubVectorStore()
        retriever = _StubKnowledgeRetriever(ep, vs)
        with pytest.raises(ValueError):
            await retriever.retrieve("   ")

    @pytest.mark.asyncio
    async def test_retrieve_returns_retrieval_result(self):
        ep = _StubEmbeddingProvider()
        vs = _StubVectorStore()
        retriever = _StubKnowledgeRetriever(ep, vs)
        chunk = _make_chunk(chunk_id="c1", content="Rahu in 10th house.")
        await retriever.ingest([chunk])
        result = await retriever.retrieve("Rahu")
        assert isinstance(result, RetrievalResult)
        assert result.query == "Rahu"

    @pytest.mark.asyncio
    async def test_retrieve_total_candidates_populated(self):
        ep = _StubEmbeddingProvider()
        vs = _StubVectorStore()
        retriever = _StubKnowledgeRetriever(ep, vs)
        chunk = _make_chunk(chunk_id="c1", content="Saturn in 7th house.")
        await retriever.ingest([chunk])
        result = await retriever.retrieve("Saturn")
        assert result.total_candidates >= 0

    @pytest.mark.asyncio
    async def test_ingest_empty_batch_is_noop(self):
        ep = _StubEmbeddingProvider()
        vs = _StubVectorStore()
        retriever = _StubKnowledgeRetriever(ep, vs)
        await retriever.ingest([])
        assert await vs.count() == 0

    def test_missing_abstract_method_raises(self):
        class _Incomplete(KnowledgeRetriever):
            async def retrieve(self, query, top_k=5, score_threshold=0.0, filter_metadata=None):
                return RetrievalResult(chunks=(), query=query)

            # ingest deliberately omitted

        with pytest.raises(TypeError):
            _Incomplete()  # type: ignore[abstract]


# ===========================================================================
# Type alias sanity checks
# ===========================================================================


class TestTypeAliases:
    def test_embedding_is_list_of_float(self):
        emb: Embedding = [0.1, 0.2, 0.3]
        assert isinstance(emb, list)

    def test_metadata_is_dict(self):
        meta: Metadata = {"key": "value", "count": 3}
        assert isinstance(meta, dict)
