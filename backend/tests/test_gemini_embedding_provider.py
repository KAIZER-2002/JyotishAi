import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from google.genai import types
from google.genai.errors import APIError

import os
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.core.config import settings
from app.domain.rag import EmbeddingException
from app.services.rag.providers.gemini_embedding_provider import (
    GeminiEmbeddingProvider,
)


@pytest.fixture
def mock_embedding_response():
    """Fixture to create a mock response matching EmbedContentResponse from the SDK."""
    mock_emb = MagicMock()
    mock_emb.values = [0.1] * 768
    mock_emb.statistics = MagicMock()
    mock_emb.statistics.token_count = 5

    mock_resp = MagicMock()
    mock_resp.embeddings = [mock_emb]
    return mock_resp


# ---------------------------------------------------------------------------
# Configuration and Initialization Tests
# ---------------------------------------------------------------------------


def test_gemini_embedding_provider_init_success() -> None:
    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiEmbeddingProvider()
        assert provider.provider_name == "gemini"
        assert provider.embedding_dimension == 768
        assert provider.model_name == "gemini-embedding-001"
        assert provider.timeout == 30


def test_gemini_embedding_provider_init_missing_key() -> None:
    with patch.object(settings, "GEMINI_API_KEY", None):
        with pytest.raises(EmbeddingException) as exc_info:
            GeminiEmbeddingProvider()
        assert "GEMINI_API_KEY is missing" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Single Embedding Tests (Sync & Async)
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_embed_single_success(mock_client_cls: MagicMock, mock_embedding_response) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.embed_content.return_value = mock_embedding_response

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        embedding = provider.embed("Hello world")

        assert embedding == [0.1] * 768
        mock_client.models.embed_content.assert_called_once_with(
            model="gemini-embedding-001",
            contents="Hello world",
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        assert provider.metrics.total_requests == 1
        assert provider.metrics.total_characters == len("Hello world")
        assert provider.metrics.total_tokens == 5


@pytest.mark.asyncio
@patch("google.genai.Client")
async def test_aembed_single_success(mock_client_cls: MagicMock, mock_embedding_response) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    
    mock_client.aio.models.embed_content = AsyncMock(return_value=mock_embedding_response)

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        embedding = await provider.aembed("Hello async")

        assert embedding == [0.1] * 768
        mock_client.aio.models.embed_content.assert_called_once_with(
            model="gemini-embedding-001",
            contents="Hello async",
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        assert provider.metrics.total_requests == 1
        assert provider.metrics.total_characters == len("Hello async")
        assert provider.metrics.total_tokens == 5


# ---------------------------------------------------------------------------
# Batch Embedding Tests (Sync & Async)
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_embed_batch_success(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    # Create mock response with 2 embeddings
    mock_emb1 = MagicMock()
    mock_emb1.values = [0.1] * 768
    mock_emb1.statistics = MagicMock()
    mock_emb1.statistics.token_count = 3

    mock_emb2 = MagicMock()
    mock_emb2.values = [0.2] * 768
    mock_emb2.statistics = MagicMock()
    mock_emb2.statistics.token_count = 4

    mock_resp = MagicMock()
    mock_resp.embeddings = [mock_emb1, mock_emb2]
    mock_client.models.embed_content.return_value = mock_resp

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        embeddings = provider.embed_batch(["text one", "text two"])

        assert len(embeddings) == 2
        assert embeddings[0] == [0.1] * 768
        assert embeddings[1] == [0.2] * 768
        mock_client.models.embed_content.assert_called_once_with(
            model="gemini-embedding-001",
            contents=["text one", "text two"],
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        assert provider.metrics.total_requests == 1
        assert provider.metrics.total_characters == len("text one") + len("text two")
        assert provider.metrics.total_tokens == 7


@pytest.mark.asyncio
@patch("google.genai.Client")
async def test_aembed_batch_success(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_emb = MagicMock()
    mock_emb.values = [0.5] * 768
    mock_emb.statistics = MagicMock()
    mock_emb.statistics.token_count = 10

    mock_resp = MagicMock()
    mock_resp.embeddings = [mock_emb]
    mock_client.aio.models.embed_content = AsyncMock(return_value=mock_resp)

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        embeddings = await provider.aembed_batch(["async batch"])

        assert len(embeddings) == 1
        assert embeddings[0] == [0.5] * 768
        mock_client.aio.models.embed_content.assert_called_once_with(
            model="gemini-embedding-001",
            contents=["async batch"],
            config=types.EmbedContentConfig(output_dimensionality=768),
        )


# ---------------------------------------------------------------------------
# Empty/Whitespace Text Validations
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_embed_empty_text_raises_value_error(mock_client_cls: MagicMock) -> None:
    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        
        with pytest.raises(ValueError) as exc:
            provider.embed("")
        assert "must be non-empty" in str(exc.value)

        with pytest.raises(ValueError) as exc:
            provider.embed("   ")
        assert "must be non-empty" in str(exc.value)

        with pytest.raises(ValueError) as exc:
            provider.embed_batch(["ok", ""])
        assert "Input text at index 1 must be non-empty" in str(exc.value)


@pytest.mark.asyncio
@patch("google.genai.Client")
async def test_aembed_empty_text_raises_value_error(mock_client_cls: MagicMock) -> None:
    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()

        with pytest.raises(ValueError) as exc:
            await provider.aembed("")
        assert "must be non-empty" in str(exc.value)

        with pytest.raises(ValueError) as exc:
            await provider.aembed_batch(["ok", "   "])
        assert "Input text at index 1 must be non-empty" in str(exc.value)


# ---------------------------------------------------------------------------
# Large Batch Chunking Behavior
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_large_batch_chunking(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    # Return 100 embeddings for the first call, 50 for the second
    mock_emb_chunk1 = [MagicMock() for _ in range(100)]
    for m in mock_emb_chunk1:
        m.values = [0.1] * 768
        m.statistics.token_count = 1
    mock_resp1 = MagicMock()
    mock_resp1.embeddings = mock_emb_chunk1

    mock_emb_chunk2 = [MagicMock() for _ in range(50)]
    for m in mock_emb_chunk2:
        m.values = [0.2] * 768
        m.statistics.token_count = 2
    mock_resp2 = MagicMock()
    mock_resp2.embeddings = mock_emb_chunk2

    mock_client.models.embed_content.side_effect = [mock_resp1, mock_resp2]

    # Create 150 text strings
    texts = [f"text-{i}" for i in range(150)]

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        embeddings = provider.embed_batch(texts)

        assert len(embeddings) == 150
        assert mock_client.models.embed_content.call_count == 2
        
        # Verify first call had 100 texts, second call had 50
        call_args_list = mock_client.models.embed_content.call_args_list
        assert len(call_args_list[0][1]["contents"]) == 100
        assert len(call_args_list[1][1]["contents"]) == 50
        
        assert provider.metrics.total_requests == 2
        assert provider.metrics.total_tokens == (100 * 1) + (50 * 2)


@pytest.mark.asyncio
@patch("google.genai.Client")
async def test_large_batch_chunking_async(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_emb_chunk1 = [MagicMock() for _ in range(100)]
    for m in mock_emb_chunk1:
        m.values = [0.1] * 768
        m.statistics.token_count = 1
    mock_resp1 = MagicMock()
    mock_resp1.embeddings = mock_emb_chunk1

    mock_emb_chunk2 = [MagicMock() for _ in range(50)]
    for m in mock_emb_chunk2:
        m.values = [0.2] * 768
        m.statistics.token_count = 2
    mock_resp2 = MagicMock()
    mock_resp2.embeddings = mock_emb_chunk2

    mock_client.aio.models.embed_content = AsyncMock(side_effect=[mock_resp1, mock_resp2])

    texts = [f"text-{i}" for i in range(150)]

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        embeddings = await provider.aembed_batch(texts)

        assert len(embeddings) == 150
        assert mock_client.aio.models.embed_content.call_count == 2


# ---------------------------------------------------------------------------
# Retry Logic and Transient Error Handling
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_retry_on_transient_error(mock_client_cls: MagicMock, mock_embedding_response) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    # First attempt raises 429 Rate Limit, second attempt succeeds
    mock_client.models.embed_content.side_effect = [
        APIError(code=429, response_json={"error": "Rate limit exceeded"}),
        mock_embedding_response,
    ]

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        
        # We patch sleep to make the retry test fast
        with patch("time.sleep", return_value=None):
            embedding = provider.embed("Transient retry test")
            assert embedding == [0.1] * 768
            assert mock_client.models.embed_content.call_count == 2


@patch("google.genai.Client")
def test_no_retry_on_permanent_error(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    # Raise a non-retryable 403 Forbidden
    mock_client.models.embed_content.side_effect = APIError(
        code=403, response_json={"error": "Permission denied"}
    )

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        
        with pytest.raises(EmbeddingException) as exc:
            provider.embed("Forbidden test")
        assert "API error occurred" in str(exc.value)
        assert mock_client.models.embed_content.call_count == 1


@patch("google.genai.Client")
def test_retry_exhaustion_raises(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    # 429 returned on all calls
    mock_client.models.embed_content.side_effect = APIError(
        code=429, response_json={"error": "Rate limit exceeded"}
    )

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        
        with patch("time.sleep", return_value=None):
            with pytest.raises(EmbeddingException) as exc:
                provider.embed("Exhaust retry test")
            assert "Rate limit exceeded" in str(exc.value)
            # Retried 3 times (first attempt + 2 retries)
            assert mock_client.models.embed_content.call_count == 3


# ---------------------------------------------------------------------------
# Timeout Handling
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_timeout_handling(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_client.models.embed_content.side_effect = httpx.TimeoutException("Timeout")

    with patch.object(settings, "GEMINI_API_KEY", "fake-key"):
        provider = GeminiEmbeddingProvider()
        
        with patch("time.sleep", return_value=None):
            with pytest.raises(EmbeddingException) as exc:
                provider.embed("Timeout test")
            assert "timed out" in str(exc.value)
