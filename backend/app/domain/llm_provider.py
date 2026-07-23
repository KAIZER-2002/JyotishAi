"""
LLM provider abstraction layer.

Provider-agnostic domain models and interface for LLM interactions.
No network calls, no Gemini, no OpenAI, no Anthropic-specific code.

All concrete providers implement LLMProvider and return LLMResponse.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, AsyncGenerator

from app.domain.prompt import StructuredPrompt


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class FinishReason(Enum):
    """
    Canonical reason why the LLM stopped generating tokens.

    Maps to the finish-reason strings returned by major providers without
    using any provider-specific value.

        STOP         — Model reached a natural stopping point (end of response).
        LENGTH       — Output was truncated at the configured max-token limit.
        CONTENT_FILTER — Output was blocked or filtered by safety systems.
        ERROR        — Generation failed due to an upstream error.
        UNKNOWN      — Provider returned an unrecognised or missing finish reason.
    """
    STOP           = "stop"
    LENGTH         = "length"
    CONTENT_FILTER = "content_filter"
    ERROR          = "error"
    UNKNOWN        = "unknown"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LLMUsage:
    """
    Token-count statistics for a single LLM request/response pair.

    Attributes
    ----------
    prompt_tokens:
        Number of tokens consumed by the input prompt.
    completion_tokens:
        Number of tokens in the generated completion.
    total_tokens:
        Sum of prompt_tokens + completion_tokens.
        Provided explicitly (rather than computed) so providers that return
        a different total (due to cached tokens, etc.) can be represented
        accurately.
    """
    prompt_tokens:     int
    completion_tokens: int
    total_tokens:      int


@dataclass(frozen=True)
class LLMRequest:
    """
    Provider-agnostic request envelope wrapping a StructuredPrompt.

    Attributes
    ----------
    prompt:
        The structured prompt to be submitted to the LLM.
    max_tokens:
        Maximum number of tokens the provider should generate.
        None means "use provider default".
    temperature:
        Sampling temperature (0.0 = deterministic, 1.0 = creative).
        None means "use provider default".
    model_hint:
        Optional provider-specific model identifier or alias.
        Providers may ignore this if they manage model selection internally.
    request_id:
        Optional caller-supplied identifier for tracing / deduplication.
    """
    prompt:     StructuredPrompt
    max_tokens: int | None   = None
    temperature: float | None = None
    model_hint: str | None   = None
    request_id: str | None   = None


@dataclass(frozen=True)
class LLMResponse:
    """
    Provider-agnostic response from an LLM completion call.

    Attributes
    ----------
    text:
        The primary generated text content.
    finish_reason:
        Why the model stopped generating.
    usage:
        Token statistics, or None if the provider did not supply them.
    model:
        The provider's identifier of the model that generated this response.
        Empty string if the provider did not return a model name.
    provider:
        A short string identifying which provider produced this response
        (e.g. "gemini", "openai").  Set by the concrete provider implementation.
    latency_ms:
        Wall-clock time in milliseconds from request dispatch to response
        receipt.  0 if not measured.
    request_id:
        Echo of the request_id supplied in LLMRequest, or None.
    raw_response:
        Opaque provider-specific payload for debugging.  Not used by any
        domain logic; must be omitted from serialised outputs.
    """
    text:          str
    finish_reason: FinishReason
    usage:         LLMUsage | None = None
    model:         str             = ""
    provider:      str             = ""
    latency_ms:    int             = 0
    request_id:    str | None      = None
    raw_response:  object          = field(default=None, compare=False, hash=False)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def succeeded(self) -> bool:
        """True when the response completed without error or filtering."""
        return self.finish_reason in (FinishReason.STOP, FinishReason.LENGTH)

    @property
    def was_filtered(self) -> bool:
        """True when the response was blocked by a content filter."""
        return self.finish_reason is FinishReason.CONTENT_FILTER

    @property
    def failed(self) -> bool:
        """True when an upstream error prevented generation."""
        return self.finish_reason is FinishReason.ERROR


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """
    Abstract base class for all LLM provider implementations.

    Concrete providers (Gemini, OpenAI, Anthropic, …) must:
      1. Subclass LLMProvider.
      2. Implement ``complete`` (sync) and/or ``acomplete`` (async).
      3. Map their provider-specific response fields to LLMResponse.
      4. Set ``provider_name`` to a short, stable identifier string.

    The interface accepts an LLMRequest (which wraps a StructuredPrompt) and
    returns an LLMResponse.  No provider-specific types leak across the boundary.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Short stable identifier for this provider (e.g. 'gemini', 'openai')."""

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Synchronous completion.

        Parameters
        ----------
        request:
            The LLMRequest to submit.

        Returns
        -------
        LLMResponse
            Provider-independent response.
        """

    @abstractmethod
    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        """
        Asynchronous completion.

        Parameters
        ----------
        request:
            The LLMRequest to submit.

        Returns
        -------
        LLMResponse
            Provider-independent response.
        """

    async def astream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """
        Asynchronous streaming completion.

        Parameters
        ----------
        request:
            The LLMRequest to submit.

        Yields
        ------
        LLMResponse
            Provider-independent partial responses/chunks.
        """
        raise NotImplementedError("astream is not implemented by this provider.")
        yield  # Make it an async generator
