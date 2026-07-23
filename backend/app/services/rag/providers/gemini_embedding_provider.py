import asyncio
from typing import Any, Optional, Sequence

import httpx
import tenacity
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import settings
from app.domain.rag import Embedding, EmbeddingProvider, EmbeddingException


class EmbeddingUsage:
    """Tracks token, character, and request counts for embedding operations."""

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.total_tokens: int = 0
        self.total_characters: int = 0

    def reset(self) -> None:
        """Reset usage metrics to zero."""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_characters = 0


def is_retryable_exception(exception: BaseException) -> bool:
    """Helper function to filter exceptions for tenacity retry logic."""
    if isinstance(exception, (httpx.TimeoutException, asyncio.TimeoutError, TimeoutError)):
        return True
    if isinstance(exception, APIError):
        # Retry on standard transient status codes (Rate Limit, Server Errors)
        if exception.code in (429, 500, 502, 503, 504):
            return True
    return False


_retry_decorator = tenacity.retry(
    reraise=True,
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception(is_retryable_exception),
)


def _handle_exception(e: Exception) -> None:
    """Maps Google/HTTPX exceptions to standard EmbeddingException."""
    if isinstance(e, (httpx.TimeoutException, asyncio.TimeoutError, TimeoutError)):
        raise EmbeddingException(f"Gemini embedding API request timed out: {str(e)}") from e
    elif isinstance(e, APIError):
        raise EmbeddingException(f"Gemini embedding API error occurred: {str(e)}") from e
    elif isinstance(e, EmbeddingException):
        raise e
    else:
        raise EmbeddingException(
            f"An unexpected error occurred while calling Gemini API: {str(e)}"
        ) from e


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Production-ready implementation of EmbeddingProvider using the Google Gemini API.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Initializes the Gemini Client for generating embeddings.

        Raises:
            EmbeddingException: If GEMINI_API_KEY is not configured or provided.
        """
        self._api_key = api_key or settings.GEMINI_API_KEY
        if not self._api_key:
            raise EmbeddingException(
                "Configuration error: GEMINI_API_KEY is missing from settings."
            )

        self.model_name = model_name or settings.GEMINI_EMBEDDING_MODEL
        self.timeout = timeout if timeout is not None else settings.GEMINI_TIMEOUT
        
        self._client = genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(timeout=self.timeout * 1000),
        )
        self._metrics = EmbeddingUsage()

    @property
    def provider_name(self) -> str:
        """Short stable identifier for this provider."""
        return "gemini"

    @property
    def embedding_dimension(self) -> int:
        """Dimensionality of the vectors produced by this provider."""
        # text-embedding-004 outputs 768-dimensional vectors by default.
        return 768

    @property
    def metrics(self) -> EmbeddingUsage:
        """Access the usage metrics tracking."""
        return self._metrics

    def embed(self, text: str) -> Embedding:
        """
        Produce a dense vector representation of a single text string.

        Parameters
        ----------
        text:
            The input string to embed. Must be non-empty.
        """
        if not text or not text.strip():
            raise ValueError("Input text to embed must be non-empty and not only whitespace.")

        @_retry_decorator
        def _embed() -> Any:
            return self._client.models.embed_content(
                model=self.model_name,
                contents=text,
            )

        try:
            response = _embed()
            if not response.embeddings:
                raise EmbeddingException("Gemini API returned an empty response.")

            token_count = 0
            if response.embeddings[0].statistics:
                token_count = response.embeddings[0].statistics.token_count or 0

            self._update_metrics(len(text), token_count)
            return response.embeddings[0].values
        except Exception as e:
            _handle_exception(e)
            raise

    async def aembed(self, text: str) -> Embedding:
        """Asynchronous variant of embed."""
        if not text or not text.strip():
            raise ValueError("Input text to embed must be non-empty and not only whitespace.")

        @_retry_decorator
        async def _aembed() -> Any:
            return await self._client.aio.models.embed_content(
                model=self.model_name,
                contents=text,
            )

        try:
            response = await _aembed()
            if not response.embeddings:
                raise EmbeddingException("Gemini API returned an empty response.")

            token_count = 0
            if response.embeddings[0].statistics:
                token_count = response.embeddings[0].statistics.token_count or 0

            self._update_metrics(len(text), token_count)
            return response.embeddings[0].values
        except Exception as e:
            _handle_exception(e)
            raise

    def embed_batch(self, texts: Sequence[str]) -> list[Embedding]:
        """Embed multiple texts in batches, chunking inputs to respect API limit thresholds."""
        if not texts:
            return []

        for idx, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Input text at index {idx} must be non-empty and not only whitespace.")

        max_batch_size = 100
        results = []

        for i in range(0, len(texts), max_batch_size):
            chunk = texts[i : i + max_batch_size]
            results.extend(self._embed_batch_chunk(chunk))

        return results

    async def aembed_batch(self, texts: Sequence[str]) -> list[Embedding]:
        """Asynchronous variant of embed_batch, invoking parallel requests for chunks."""
        if not texts:
            return []

        for idx, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Input text at index {idx} must be non-empty and not only whitespace.")

        max_batch_size = 100
        tasks = []

        for i in range(0, len(texts), max_batch_size):
            chunk = texts[i : i + max_batch_size]
            tasks.append(self._aembed_batch_chunk(chunk))

        chunk_results = await asyncio.gather(*tasks)

        results = []
        for r in chunk_results:
            results.extend(r)
        return results

    def _embed_batch_chunk(self, texts: Sequence[str]) -> list[Embedding]:
        """Performs a single synchronous batch request."""
        @_retry_decorator
        def _embed_chunk() -> Any:
            return self._client.models.embed_content(
                model=self.model_name,
                contents=list(texts),
            )

        try:
            response = _embed_chunk()
            if not response.embeddings:
                raise EmbeddingException("Gemini API returned an empty response.")
            if len(response.embeddings) != len(texts):
                raise EmbeddingException(
                    f"Mismatched embedding count: expected {len(texts)}, got {len(response.embeddings)}"
                )

            total_tokens = 0
            for emb in response.embeddings:
                if emb.statistics:
                    total_tokens += emb.statistics.token_count or 0

            self._update_metrics(sum(len(t) for t in texts), total_tokens)
            return [emb.values for emb in response.embeddings]
        except Exception as e:
            _handle_exception(e)
            raise

    async def _aembed_batch_chunk(self, texts: Sequence[str]) -> list[Embedding]:
        """Performs a single asynchronous batch request."""
        @_retry_decorator
        async def _aembed_chunk() -> Any:
            return await self._client.aio.models.embed_content(
                model=self.model_name,
                contents=list(texts),
            )

        try:
            response = await _aembed_chunk()
            if not response.embeddings:
                raise EmbeddingException("Gemini API returned an empty response.")
            if len(response.embeddings) != len(texts):
                raise EmbeddingException(
                    f"Mismatched embedding count: expected {len(texts)}, got {len(response.embeddings)}"
                )

            total_tokens = 0
            for emb in response.embeddings:
                if emb.statistics:
                    total_tokens += emb.statistics.token_count or 0

            self._update_metrics(sum(len(t) for t in texts), total_tokens)
            return [emb.values for emb in response.embeddings]
        except Exception as e:
            _handle_exception(e)
            raise

    def _update_metrics(self, char_count: int, token_count: int) -> None:
        """Update metrics attributes in a thread-safe / transaction-safe manner."""
        self._metrics.total_requests += 1
        self._metrics.total_characters += char_count
        self._metrics.total_tokens += token_count
