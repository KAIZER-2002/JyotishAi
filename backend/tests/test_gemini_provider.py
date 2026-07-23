import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from google.genai.errors import APIError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.domain.llm_provider import FinishReason
from app.domain.prompt import PromptMessage, PromptRole, StructuredPrompt
from app.exceptions.llm import GeminiProviderException
from app.services.llm.providers.gemini_provider import GeminiProvider, map_finish_reason


def _minimal_prompt() -> StructuredPrompt:
    return StructuredPrompt(
        sections=(),
        messages=(
            PromptMessage(role=PromptRole.SYSTEM, content="System prompt"),
            PromptMessage(role=PromptRole.USER, content="Hello"),
        ),
        metadata=(),
    )


# ---------------------------------------------------------------------------
# Finish Reason Mapping Tests
# ---------------------------------------------------------------------------


def test_map_finish_reason_stop() -> None:
    assert map_finish_reason("STOP") == FinishReason.STOP
    assert map_finish_reason("stop") == FinishReason.STOP


def test_map_finish_reason_length() -> None:
    assert map_finish_reason("MAX_TOKENS") == FinishReason.LENGTH
    assert map_finish_reason("LENGTH") == FinishReason.LENGTH


def test_map_finish_reason_safety() -> None:
    assert map_finish_reason("SAFETY") == FinishReason.CONTENT_FILTER
    assert map_finish_reason("BLOCKLIST") == FinishReason.CONTENT_FILTER
    assert map_finish_reason("PROHIBITED_CONTENT") == FinishReason.CONTENT_FILTER


def test_map_finish_reason_error() -> None:
    assert map_finish_reason("ERROR") == FinishReason.ERROR


def test_map_finish_reason_unknown() -> None:
    assert map_finish_reason(None) == FinishReason.UNKNOWN
    assert map_finish_reason("INVALID_VALUE") == FinishReason.UNKNOWN


# ---------------------------------------------------------------------------
# Initialization / Configuration Tests
# ---------------------------------------------------------------------------


def test_gemini_provider_init_missing_key() -> None:
    with patch.object(settings, "GEMINI_API_KEY", None):
        with pytest.raises(GeminiProviderException) as exc_info:
            GeminiProvider()
        assert "GEMINI_API_KEY is missing" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Execution Tests (Sync & Async Completion)
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_gemini_provider_complete_success(mock_client_cls: MagicMock) -> None:
    # Setup mock response
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.model_version = "gemini-2.5-flash"

    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.content.parts = [MagicMock(text="Hello back!")]

    mock_response.candidates = [mock_candidate]
    mock_response.usage_metadata.prompt_token_count = 10
    mock_response.usage_metadata.response_token_count = 20
    mock_response.usage_metadata.total_token_count = 30

    mock_client.models.generate_content.return_value = mock_response

    # Test
    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiProvider()
        from app.domain.llm_provider import LLMRequest

        request = LLMRequest(
            prompt=_minimal_prompt(),
            temperature=0.5,
            max_tokens=100,
            model_hint="gemini-2.0-flash",
            request_id="req-123",
        )

        response = provider.complete(request)

        # Assertions
        assert response.text == "Hello back!"
        assert response.finish_reason == FinishReason.STOP
        assert response.usage is not None
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30
        assert response.model == "gemini-2.5-flash"
        assert response.provider == "gemini"
        assert response.request_id == "req-123"

        # Verify Client call config/payload matching
        mock_client.models.generate_content.assert_called_once()
        kwargs = mock_client.models.generate_content.call_args[1]
        assert kwargs["model"] == "gemini-2.0-flash"
        assert len(kwargs["contents"]) == 1
        assert kwargs["contents"][0].role == "user"
        assert kwargs["config"].system_instruction == "System prompt"
        assert kwargs["config"].temperature == 0.5
        assert kwargs["config"].max_output_tokens == 100


@patch("google.genai.Client")
def test_gemini_provider_acomplete_success(mock_client_cls: MagicMock) -> None:
    # Setup mock response
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.model_version = "gemini-2.5-flash"

    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.content.parts = [MagicMock(text="Hello back async!")]

    mock_response.candidates = [mock_candidate]
    mock_response.usage_metadata.prompt_token_count = 15
    mock_response.usage_metadata.response_token_count = 25
    mock_response.usage_metadata.total_token_count = 40

    # Async generate method
    mock_aio = MagicMock()
    mock_client.aio = mock_aio
    mock_aio.models.generate_content = AsyncMock(return_value=mock_response)

    # Test
    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiProvider()
        from app.domain.llm_provider import LLMRequest

        request = LLMRequest(
            prompt=_minimal_prompt(),
            temperature=0.7,
            max_tokens=200,
            model_hint="gemini-2.0-flash",
            request_id="req-456",
        )

        response = asyncio.run(provider.acomplete(request))

        # Assertions
        assert response.text == "Hello back async!"
        assert response.finish_reason == FinishReason.STOP
        assert response.usage is not None
        assert response.usage.prompt_tokens == 15
        assert response.usage.completion_tokens == 25
        assert response.usage.total_tokens == 40
        assert response.model == "gemini-2.5-flash"
        assert response.provider == "gemini"
        assert response.request_id == "req-456"


# ---------------------------------------------------------------------------
# API Error and Timeout Handling Tests
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_gemini_provider_api_error(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.side_effect = APIError(
        code=429, response_json={"error": "Quota exceeded"}
    )

    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiProvider()
        from app.domain.llm_provider import LLMRequest

        request = LLMRequest(prompt=_minimal_prompt())
        with pytest.raises(GeminiProviderException) as exc_info:
            provider.complete(request)
        assert "Gemini API error occurred" in str(exc_info.value)


@patch("google.genai.Client")
def test_gemini_provider_timeout_error(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    # Simulate a network/httpx timeout
    mock_client.models.generate_content.side_effect = httpx.TimeoutException("Read timeout")

    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiProvider()
        from app.domain.llm_provider import LLMRequest

        request = LLMRequest(prompt=_minimal_prompt())
        with pytest.raises(GeminiProviderException) as exc_info:
            provider.complete(request)
        assert "timed out" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Content Filtering / Safety Tests
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_gemini_provider_content_filtered_candidate(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "SAFETY"
    mock_candidate.content.parts = []
    mock_response.candidates = [mock_candidate]
    mock_response.usage_metadata = None

    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiProvider()
        from app.domain.llm_provider import LLMRequest

        request = LLMRequest(prompt=_minimal_prompt())
        response = provider.complete(request)

        assert response.finish_reason == FinishReason.CONTENT_FILTER
        assert response.text == ""
        assert response.was_filtered is True


@patch("google.genai.Client")
def test_gemini_provider_content_filtered_prompt(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.candidates = []
    mock_response.prompt_feedback.block_reason = "SAFETY"
    mock_response.usage_metadata = None

    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiProvider()
        from app.domain.llm_provider import LLMRequest

        request = LLMRequest(prompt=_minimal_prompt())
        response = provider.complete(request)

        assert response.finish_reason == FinishReason.CONTENT_FILTER
        assert response.text == ""
        assert response.was_filtered is True


# ---------------------------------------------------------------------------
# Empty/Invalid Response Tests
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_gemini_provider_empty_response(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = None

    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiProvider()
        from app.domain.llm_provider import LLMRequest

        request = LLMRequest(prompt=_minimal_prompt())
        with pytest.raises(GeminiProviderException) as exc_info:
            provider.complete(request)
        assert "empty response" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Payload Verification Tests
# ---------------------------------------------------------------------------


@patch("google.genai.Client")
def test_gemini_provider_missing_user_message_raises(mock_client_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    with patch.object(settings, "GEMINI_API_KEY", "fake-api-key"):
        provider = GeminiProvider()
        from app.domain.llm_provider import LLMRequest

        # Prompt with only system instruction and no user messages
        prompt = StructuredPrompt(
            sections=(),
            messages=(PromptMessage(role=PromptRole.SYSTEM, content="system content"),),
            metadata=(),
        )
        request = LLMRequest(prompt=prompt)

        with pytest.raises(GeminiProviderException) as exc_info:
            provider.complete(request)
        assert "requires at least one user message" in str(exc_info.value)
