import asyncio
import time
from typing import Any, Optional, AsyncGenerator

import httpx
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import settings
from app.domain.llm_provider import FinishReason, LLMProvider, LLMRequest, LLMResponse, LLMUsage
from app.domain.prompt import PromptRole
from app.exceptions.llm import GeminiProviderException
from app.services.llm.base import BaseLLMProvider
from app.services.llm.registry import provider_registry


def map_finish_reason(gemini_reason: Any) -> FinishReason:
    """Maps Gemini API finish reason to provider-agnostic FinishReason."""
    if not gemini_reason:
        return FinishReason.UNKNOWN

    reason_str = str(gemini_reason).upper()
    if "STOP" in reason_str:
        return FinishReason.STOP
    if "MAX_TOKENS" in reason_str or "LENGTH" in reason_str:
        return FinishReason.LENGTH
    if any(r in reason_str for r in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII")):
        return FinishReason.CONTENT_FILTER
    if "ERROR" in reason_str:
        return FinishReason.ERROR
    return FinishReason.UNKNOWN


@provider_registry.register("gemini")
class GeminiProvider(LLMProvider, BaseLLMProvider):
    """
    Gemini LLM Provider implementing the new LLMProvider contract
    while maintaining backward compatibility with BaseLLMProvider.
    """

    def __init__(self) -> None:
        """
        Initializes the Gemini client.

        Raises:
            GeminiProviderException: If GEMINI_API_KEY is not set.
        """
        if not settings.GEMINI_API_KEY:
            raise GeminiProviderException(
                "Configuration error: GEMINI_API_KEY is missing from settings."
            )

        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @property
    def provider_name(self) -> str:
        """Returns the unique identifier for this provider."""
        return "gemini"

    def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Synchronous completion using the Google Gemini API.
        """
        model = request.model_hint or settings.GEMINI_MODEL
        if model in ("gemini-2.5-flash", "gemini-2.0-flash", "text-davinci-003"):
            model = settings.GEMINI_MODEL

        contents, system_instruction = self._prepare_payload(request)
        config = self._prepare_config(request, system_instruction)

        start_time = time.perf_counter()
        try:
            response = self._client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return self._build_response(request, response, model, latency_ms)

        except Exception as primary_err:
            if model != settings.GEMINI_MODEL:
                try:
                    response = self._client.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=contents,
                        config=config,
                    )
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    return self._build_response(request, response, settings.GEMINI_MODEL, latency_ms)
                except Exception:
                    pass

            if isinstance(primary_err, httpx.TimeoutException):
                raise GeminiProviderException(f"Gemini API request timed out: {str(primary_err)}") from primary_err
            elif isinstance(primary_err, (asyncio.TimeoutError, TimeoutError)):
                raise GeminiProviderException(f"Gemini API request timed out: {str(primary_err)}") from primary_err
            elif isinstance(primary_err, APIError):
                raise GeminiProviderException(f"Gemini API error occurred: {str(primary_err)}") from primary_err
            else:
                raise GeminiProviderException(
                    f"An unexpected error occurred while calling Gemini API: {str(primary_err)}"
                ) from primary_err

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        """
        Asynchronous completion using the Google Gemini API.
        """
        model = request.model_hint or settings.GEMINI_MODEL
        if model in ("gemini-2.5-flash", "gemini-2.0-flash", "text-davinci-003"):
            model = settings.GEMINI_MODEL

        contents, system_instruction = self._prepare_payload(request)
        config = self._prepare_config(request, system_instruction)

        start_time = time.perf_counter()
        try:
            response = await self._client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return self._build_response(request, response, model, latency_ms)

        except Exception as primary_err:
            if model != settings.GEMINI_MODEL:
                try:
                    response = await self._client.aio.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=contents,
                        config=config,
                    )
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    return self._build_response(request, response, settings.GEMINI_MODEL, latency_ms)
                except Exception:
                    pass

            if isinstance(primary_err, httpx.TimeoutException):
                raise GeminiProviderException(f"Gemini API request timed out: {str(primary_err)}") from primary_err
            elif isinstance(primary_err, (asyncio.TimeoutError, TimeoutError)):
                raise GeminiProviderException(f"Gemini API request timed out: {str(primary_err)}") from primary_err
            elif isinstance(primary_err, APIError):
                raise GeminiProviderException(f"Gemini API error occurred: {str(primary_err)}") from primary_err
            else:
                raise GeminiProviderException(
                    f"An unexpected error occurred while calling Gemini API: {str(primary_err)}"
                ) from primary_err

    async def astream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """
        Asynchronous streaming completion using the Google Gemini API.
        """
        model = request.model_hint or settings.GEMINI_MODEL
        # Normalize deprecated model names to active working model
        if model in ("gemini-2.5-flash", "gemini-2.0-flash", "text-davinci-003"):
            model = settings.GEMINI_MODEL

        contents, system_instruction = self._prepare_payload(request)
        config = self._prepare_config(request, system_instruction)

        start_time = time.perf_counter()
        try:
            async for response in await self._client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            ):
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                yield self._build_response(request, response, model, latency_ms)

        except Exception as primary_err:
            # Fallback to default GEMINI_MODEL if custom model failed
            if model != settings.GEMINI_MODEL:
                try:
                    async for response in await self._client.aio.models.generate_content_stream(
                        model=settings.GEMINI_MODEL,
                        contents=contents,
                        config=config,
                    ):
                        latency_ms = int((time.perf_counter() - start_time) * 1000)
                        yield self._build_response(request, response, settings.GEMINI_MODEL, latency_ms)
                    return
                except Exception:
                    pass

            if isinstance(primary_err, httpx.TimeoutException):
                raise GeminiProviderException(f"Gemini API request timed out: {str(primary_err)}") from primary_err
            elif isinstance(primary_err, (asyncio.TimeoutError, TimeoutError)):
                raise GeminiProviderException(f"Gemini API request timed out: {str(primary_err)}") from primary_err
            elif isinstance(primary_err, APIError):
                raise GeminiProviderException(f"Gemini API error occurred: {str(primary_err)}") from primary_err
            else:
                raise GeminiProviderException(
                    f"An unexpected error occurred while calling Gemini API: {str(primary_err)}"
                ) from primary_err

    async def generate(
        self,
        *,
        message: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        Generates a response to maintain compatibility with BaseLLMProvider.
        """
        from app.domain.prompt import PromptMessage, StructuredPrompt

        messages = []
        if system_prompt:
            messages.append(PromptMessage(role=PromptRole.SYSTEM, content=system_prompt))
        messages.append(PromptMessage(role=PromptRole.USER, content=message))

        prompt = StructuredPrompt(
            sections=(),
            messages=tuple(messages),
            metadata=(),
        )
        request = LLMRequest(
            prompt=prompt,
            temperature=temperature,
            model_hint=model,
        )
        response = await self.acomplete(request)
        return response.text

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prepare_payload(self, request: LLMRequest) -> tuple[list[types.Content], Optional[str]]:
        system_instruction = None
        raw_messages: list[tuple[str, str]] = []

        for msg in request.prompt.messages:
            if msg.role == PromptRole.SYSTEM:
                system_instruction = msg.content
            else:
                role = "user" if msg.role == PromptRole.USER else "model"
                if msg.content and msg.content.strip():
                    raw_messages.append((role, msg.content.strip()))

        if not raw_messages:
            raise GeminiProviderException("Gemini API request requires at least one user message.")

        # Sanitize role transitions: Merge consecutive messages with the same role
        sanitized_contents: list[types.Content] = []
        for role, text in raw_messages:
            if sanitized_contents and sanitized_contents[-1].role == role:
                existing_text = sanitized_contents[-1].parts[0].text or ""
                sanitized_contents[-1].parts = [types.Part(text=f"{existing_text}\n\n{text}")]
            else:
                sanitized_contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=text)],
                    )
                )

        # Ensure the conversation starts with a 'user' message
        if sanitized_contents and sanitized_contents[0].role != "user":
            sanitized_contents.pop(0)

        if not sanitized_contents:
            raise GeminiProviderException("Gemini API request requires at least one user message.")

        return sanitized_contents, system_instruction

    def _prepare_config(
        self, request: LLMRequest, system_instruction: Optional[str]
    ) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=request.temperature if request.temperature is not None else None,
            max_output_tokens=request.max_tokens if request.max_tokens is not None else None,
        )

    def _build_response(
        self, request: LLMRequest, response: Any, model: str, latency_ms: int
    ) -> LLMResponse:
        if not response:
            raise GeminiProviderException("Gemini API returned an empty response.")

        candidates = response.candidates
        if not candidates:
            # Handle prompt feedback or filter blocking
            is_blocked = False
            if response.prompt_feedback and hasattr(response.prompt_feedback, "block_reason"):
                if response.prompt_feedback.block_reason:
                    is_blocked = True

            finish_reason = FinishReason.CONTENT_FILTER if is_blocked else FinishReason.UNKNOWN
            return LLMResponse(
                text="",
                finish_reason=finish_reason,
                model=response.model_version or model,
                provider="gemini",
                latency_ms=latency_ms,
                request_id=request.request_id,
                raw_response=response,
            )

        candidate = candidates[0]
        finish_reason = map_finish_reason(getattr(candidate, "finish_reason", None))

        if finish_reason == FinishReason.CONTENT_FILTER:
            return LLMResponse(
                text="",
                finish_reason=finish_reason,
                model=response.model_version or model,
                provider="gemini",
                latency_ms=latency_ms,
                request_id=request.request_id,
                raw_response=response,
            )

        text = ""
        if candidate.content and candidate.content.parts:
            parts_text = [part.text for part in candidate.content.parts if part.text is not None]
            text = "".join(parts_text)

        usage = None
        if getattr(response, "usage_metadata", None):
            um = response.usage_metadata
            p_tok = getattr(um, "prompt_token_count", 0) or 0
            c_tok = getattr(um, "candidates_token_count", 0) or getattr(um, "response_token_count", 0) or 0
            t_tok = getattr(um, "total_token_count", 0) or (p_tok + c_tok)
            usage = LLMUsage(
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
                total_tokens=t_tok,
            )

        return LLMResponse(
            text=text,
            finish_reason=finish_reason,
            usage=usage,
            model=response.model_version or model,
            provider="gemini",
            latency_ms=latency_ms,
            request_id=request.request_id,
            raw_response=response,
        )
