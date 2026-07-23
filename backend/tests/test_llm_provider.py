"""
Unit tests for the LLM provider abstraction layer.

Coverage:
  - FinishReason enum values
  - LLMUsage construction and fields
  - LLMRequest construction with defaults and overrides
  - LLMResponse construction, convenience properties, raw_response excluded from equality
  - LLMProvider ABC enforces implement-me methods
  - StubLLMProvider satisfies the contract (sync + async)
  - provider_name is exposed correctly
  - LLMResponse.succeeded / was_filtered / failed for all FinishReasons
  - LLMResponse equality ignores raw_response
  - LLMRequest carries StructuredPrompt unchanged
  - LLMUsage total_tokens is stored as supplied (not recomputed)
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.chart import Chart
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.llm_provider import (
    FinishReason,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)
from app.domain.nakshatra import Nakshatra
from app.domain.prompt import (
    PromptMessage,
    PromptRole,
    PromptSection,
    PromptSectionType,
    StructuredPrompt,
)
from app.domain.zodiac import ZodiacSign


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_prompt() -> StructuredPrompt:
    """Smallest valid StructuredPrompt for injection into requests."""
    return StructuredPrompt(
        sections=(
            PromptSection(
                section_type=PromptSectionType.INSTRUCTION,
                heading="System Instruction",
                body="You are a test assistant.",
            ),
        ),
        messages=(
            PromptMessage(role=PromptRole.SYSTEM, content="You are a test assistant."),
            PromptMessage(role=PromptRole.USER,   content="Hello."),
        ),
        metadata=(("builder_version", "1.0"),),
    )


def _usage(prompt: int = 10, completion: int = 20, total: int = 30) -> LLMUsage:
    return LLMUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
    )


def _response(
    text: str = "Test response.",
    finish_reason: FinishReason = FinishReason.STOP,
    **kwargs,
) -> LLMResponse:
    return LLMResponse(text=text, finish_reason=finish_reason, **kwargs)


# ---------------------------------------------------------------------------
# Stub provider (satisfies ABC without network calls)
# ---------------------------------------------------------------------------


class StubLLMProvider(LLMProvider):
    """
    Minimal concrete implementation used for testing the interface contract.
    Returns a pre-configured LLMResponse without any I/O.
    """

    def __init__(
        self,
        canned_text: str = "Stub response.",
        canned_finish: FinishReason = FinishReason.STOP,
    ) -> None:
        self._canned_text   = canned_text
        self._canned_finish = canned_finish

    @property
    def provider_name(self) -> str:
        return "stub"

    def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            text=self._canned_text,
            finish_reason=self._canned_finish,
            model="stub-model-1.0",
            provider=self.provider_name,
            usage=_usage(),
            request_id=request.request_id,
        )

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        return self.complete(request)


# ---------------------------------------------------------------------------
# FinishReason
# ---------------------------------------------------------------------------


def test_finish_reason_stop_value() -> None:
    assert FinishReason.STOP.value == "stop"


def test_finish_reason_length_value() -> None:
    assert FinishReason.LENGTH.value == "length"


def test_finish_reason_content_filter_value() -> None:
    assert FinishReason.CONTENT_FILTER.value == "content_filter"


def test_finish_reason_error_value() -> None:
    assert FinishReason.ERROR.value == "error"


def test_finish_reason_unknown_value() -> None:
    assert FinishReason.UNKNOWN.value == "unknown"


def test_finish_reason_all_members_present() -> None:
    names = {m.name for m in FinishReason}
    assert names == {"STOP", "LENGTH", "CONTENT_FILTER", "ERROR", "UNKNOWN"}


# ---------------------------------------------------------------------------
# LLMUsage
# ---------------------------------------------------------------------------


def test_llm_usage_fields_stored_correctly() -> None:
    usage = _usage(prompt=100, completion=200, total=300)
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 200
    assert usage.total_tokens == 300


def test_llm_usage_total_not_recomputed() -> None:
    """total_tokens is stored as supplied; provider may differ from sum."""
    usage = LLMUsage(prompt_tokens=5, completion_tokens=5, total_tokens=99)
    assert usage.total_tokens == 99


def test_llm_usage_is_frozen() -> None:
    usage = _usage()
    try:
        usage.prompt_tokens = 999  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


# ---------------------------------------------------------------------------
# LLMRequest
# ---------------------------------------------------------------------------


def test_llm_request_stores_prompt() -> None:
    prompt = _minimal_prompt()
    req = LLMRequest(prompt=prompt)
    assert req.prompt is prompt


def test_llm_request_defaults_are_none() -> None:
    req = LLMRequest(prompt=_minimal_prompt())
    assert req.max_tokens  is None
    assert req.temperature is None
    assert req.model_hint  is None
    assert req.request_id  is None


def test_llm_request_overrides_stored() -> None:
    req = LLMRequest(
        prompt=_minimal_prompt(),
        max_tokens=512,
        temperature=0.3,
        model_hint="gemini-2.5-pro",
        request_id="req-abc-123",
    )
    assert req.max_tokens   == 512
    assert req.temperature  == 0.3
    assert req.model_hint   == "gemini-2.5-pro"
    assert req.request_id   == "req-abc-123"


def test_llm_request_is_frozen() -> None:
    req = LLMRequest(prompt=_minimal_prompt())
    try:
        req.max_tokens = 1024  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


# ---------------------------------------------------------------------------
# LLMResponse
# ---------------------------------------------------------------------------


def test_llm_response_stores_text() -> None:
    r = _response("Hello, world.")
    assert r.text == "Hello, world."


def test_llm_response_stores_finish_reason() -> None:
    r = _response(finish_reason=FinishReason.LENGTH)
    assert r.finish_reason == FinishReason.LENGTH


def test_llm_response_defaults() -> None:
    r = _response()
    assert r.usage       is None
    assert r.model       == ""
    assert r.provider    == ""
    assert r.latency_ms  == 0
    assert r.request_id  is None
    assert r.raw_response is None


def test_llm_response_all_fields() -> None:
    r = LLMResponse(
        text="response",
        finish_reason=FinishReason.STOP,
        usage=_usage(),
        model="model-x",
        provider="openai",
        latency_ms=250,
        request_id="r-1",
        raw_response={"raw": "data"},
    )
    assert r.model       == "model-x"
    assert r.provider    == "openai"
    assert r.latency_ms  == 250
    assert r.request_id  == "r-1"
    assert r.raw_response == {"raw": "data"}


def test_llm_response_is_frozen() -> None:
    r = _response()
    try:
        r.text = "mutated"  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


# ---------------------------------------------------------------------------
# LLMResponse convenience properties
# ---------------------------------------------------------------------------


def test_succeeded_true_for_stop() -> None:
    assert _response(finish_reason=FinishReason.STOP).succeeded is True


def test_succeeded_true_for_length() -> None:
    assert _response(finish_reason=FinishReason.LENGTH).succeeded is True


def test_succeeded_false_for_error() -> None:
    assert _response(finish_reason=FinishReason.ERROR).succeeded is False


def test_succeeded_false_for_content_filter() -> None:
    assert _response(finish_reason=FinishReason.CONTENT_FILTER).succeeded is False


def test_was_filtered_true_for_content_filter() -> None:
    assert _response(finish_reason=FinishReason.CONTENT_FILTER).was_filtered is True


def test_was_filtered_false_for_stop() -> None:
    assert _response(finish_reason=FinishReason.STOP).was_filtered is False


def test_failed_true_for_error() -> None:
    assert _response(finish_reason=FinishReason.ERROR).failed is True


def test_failed_false_for_stop() -> None:
    assert _response(finish_reason=FinishReason.STOP).failed is False


def test_failed_false_for_unknown() -> None:
    assert _response(finish_reason=FinishReason.UNKNOWN).failed is False


# ---------------------------------------------------------------------------
# LLMResponse equality ignores raw_response
# ---------------------------------------------------------------------------


def test_llm_response_equality_ignores_raw_response() -> None:
    r1 = LLMResponse(text="hi", finish_reason=FinishReason.STOP, raw_response={"a": 1})
    r2 = LLMResponse(text="hi", finish_reason=FinishReason.STOP, raw_response={"b": 99})
    assert r1 == r2


def test_llm_response_inequality_on_text() -> None:
    r1 = LLMResponse(text="hello", finish_reason=FinishReason.STOP)
    r2 = LLMResponse(text="world", finish_reason=FinishReason.STOP)
    assert r1 != r2


# ---------------------------------------------------------------------------
# LLMProvider ABC enforcement
# ---------------------------------------------------------------------------


def test_cannot_instantiate_abstract_provider() -> None:
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_incomplete_provider_missing_complete_raises() -> None:
    class IncompleteProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "incomplete"

        async def acomplete(self, request: LLMRequest) -> LLMResponse:  # type: ignore[override]
            return _response()

    with pytest.raises(TypeError):
        IncompleteProvider()  # type: ignore[abstract]


def test_incomplete_provider_missing_acomplete_raises() -> None:
    class IncompleteProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "incomplete"

        def complete(self, request: LLMRequest) -> LLMResponse:
            return _response()

    with pytest.raises(TypeError):
        IncompleteProvider()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# StubLLMProvider — sync
# ---------------------------------------------------------------------------


def test_stub_provider_name() -> None:
    assert StubLLMProvider().provider_name == "stub"


def test_stub_complete_returns_llm_response() -> None:
    req = LLMRequest(prompt=_minimal_prompt())
    result = StubLLMProvider().complete(req)
    assert isinstance(result, LLMResponse)


def test_stub_complete_text_matches_canned() -> None:
    stub = StubLLMProvider(canned_text="Canned answer.")
    req  = LLMRequest(prompt=_minimal_prompt())
    result = stub.complete(req)
    assert result.text == "Canned answer."


def test_stub_complete_finish_reason() -> None:
    stub = StubLLMProvider(canned_finish=FinishReason.LENGTH)
    req  = LLMRequest(prompt=_minimal_prompt())
    result = stub.complete(req)
    assert result.finish_reason == FinishReason.LENGTH


def test_stub_complete_echoes_request_id() -> None:
    req = LLMRequest(prompt=_minimal_prompt(), request_id="trace-42")
    result = StubLLMProvider().complete(req)
    assert result.request_id == "trace-42"


def test_stub_complete_provider_field() -> None:
    result = StubLLMProvider().complete(LLMRequest(prompt=_minimal_prompt()))
    assert result.provider == "stub"


def test_stub_complete_usage_present() -> None:
    result = StubLLMProvider().complete(LLMRequest(prompt=_minimal_prompt()))
    assert result.usage is not None
    assert isinstance(result.usage, LLMUsage)


def test_stub_complete_succeeded() -> None:
    result = StubLLMProvider().complete(LLMRequest(prompt=_minimal_prompt()))
    assert result.succeeded is True


# ---------------------------------------------------------------------------
# StubLLMProvider — async
# ---------------------------------------------------------------------------


def test_stub_acomplete_returns_llm_response() -> None:
    req    = LLMRequest(prompt=_minimal_prompt())
    result = asyncio.run(StubLLMProvider().acomplete(req))
    assert isinstance(result, LLMResponse)


def test_stub_acomplete_text_matches_canned() -> None:
    stub   = StubLLMProvider(canned_text="Async canned.")
    req    = LLMRequest(prompt=_minimal_prompt())
    result = asyncio.run(stub.acomplete(req))
    assert result.text == "Async canned."


def test_stub_acomplete_echoes_request_id() -> None:
    req    = LLMRequest(prompt=_minimal_prompt(), request_id="async-99")
    result = asyncio.run(StubLLMProvider().acomplete(req))
    assert result.request_id == "async-99"


# ---------------------------------------------------------------------------
# Prompt round-trip through request
# ---------------------------------------------------------------------------


def test_request_prompt_preserved_in_complete() -> None:
    """StructuredPrompt must be accessible from the request inside complete()."""
    received: list[LLMRequest] = []

    class InspectingProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "inspector"

        def complete(self, request: LLMRequest) -> LLMResponse:
            received.append(request)
            return _response()

        async def acomplete(self, request: LLMRequest) -> LLMResponse:
            return self.complete(request)

    prompt = _minimal_prompt()
    req    = LLMRequest(prompt=prompt)
    InspectingProvider().complete(req)

    assert len(received) == 1
    assert received[0].prompt is prompt


def test_request_chat_dicts_accessible_inside_provider() -> None:
    """Provider can call to_chat_dicts() on the prompt without any adapter."""
    prompt = _minimal_prompt()
    dicts  = prompt.to_chat_dicts()
    assert len(dicts) == 2
    assert all("role" in d and "content" in d for d in dicts)
