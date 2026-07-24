import time
from typing import AsyncGenerator, Optional, Any
from openai import AsyncOpenAI, OpenAI

from app.core.config import settings
from app.domain.llm_provider import FinishReason, LLMProvider, LLMRequest, LLMResponse, LLMUsage
from app.domain.prompt import PromptRole
from app.exceptions.llm import ProviderException
from app.services.llm.base import BaseLLMProvider
from app.services.llm.registry import provider_registry


class OpenAIProviderException(ProviderException):
    """Exception raised by OpenAIProvider."""
    pass


def map_openai_finish_reason(reason: Optional[str]) -> FinishReason:
    if not reason:
        return FinishReason.UNKNOWN
    r = reason.lower()
    if r == "stop":
        return FinishReason.STOP
    if r in ("length", "max_tokens"):
        return FinishReason.LENGTH
    if "content" in r or "filter" in r:
        return FinishReason.CONTENT_FILTER
    return FinishReason.UNKNOWN


@provider_registry.register("openai")
class OpenAIProvider(LLMProvider, BaseLLMProvider):
    """OpenAI LLM Provider supporting sync, async, and streaming completions."""

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise OpenAIProviderException("Configuration error: OPENAI_API_KEY is missing.")
        self._sync_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @property
    def provider_name(self) -> str:
        return "openai"

    def _prepare_messages(self, request: LLMRequest):
        messages = []
        if request.prompt and hasattr(request.prompt, "messages"):
            for m in request.prompt.messages:
                role = "user"
                if m.role == PromptRole.SYSTEM:
                    role = "system"
                elif m.role == PromptRole.ASSISTANT:
                    role = "assistant"
                messages.append({"role": role, "content": m.content})
        return messages

    def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model_hint or "gpt-4o-mini"
        messages = self._prepare_messages(request)
        start_time = time.perf_counter()
        try:
            res = self._sync_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
            )
            latency = int((time.perf_counter() - start_time) * 1000)
            choice = res.choices[0]
            usage = LLMUsage(
                prompt_tokens=res.usage.prompt_tokens if res.usage else 0,
                completion_tokens=res.usage.completion_tokens if res.usage else 0,
                total_tokens=res.usage.total_tokens if res.usage else 0,
            )
            return LLMResponse(
                text=choice.message.content or "",
                finish_reason=map_openai_finish_reason(choice.finish_reason),
                usage=usage,
                raw_response=res.model_dump(),
                model=model,
                latency_ms=latency,
            )
        except Exception as e:
            raise OpenAIProviderException(f"OpenAI API error: {str(e)}") from e

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        model = request.model_hint or "gpt-4o-mini"
        messages = self._prepare_messages(request)
        start_time = time.perf_counter()
        try:
            res = await self._async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
            )
            latency = int((time.perf_counter() - start_time) * 1000)
            choice = res.choices[0]
            usage = LLMUsage(
                prompt_tokens=res.usage.prompt_tokens if res.usage else 0,
                completion_tokens=res.usage.completion_tokens if res.usage else 0,
                total_tokens=res.usage.total_tokens if res.usage else 0,
            )
            return LLMResponse(
                text=choice.message.content or "",
                finish_reason=map_openai_finish_reason(choice.finish_reason),
                usage=usage,
                raw_response=res.model_dump(),
                model=model,
                latency_ms=latency,
            )
        except Exception as e:
            raise OpenAIProviderException(f"OpenAI API error: {str(e)}") from e

    async def astream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        model = request.model_hint or "gpt-4o-mini"
        messages = self._prepare_messages(request)
        start_time = time.perf_counter()
        try:
            stream = await self._async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta.content or ""
                    finish = chunk.choices[0].finish_reason
                    latency = int((time.perf_counter() - start_time) * 1000)
                    yield LLMResponse(
                        text=delta,
                        finish_reason=map_openai_finish_reason(finish),
                        model=model,
                        latency_ms=latency,
                    )
        except Exception as e:
            raise OpenAIProviderException(f"OpenAI Streaming error: {str(e)}") from e

    async def generate(self, *, message: str, model: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        res = await self._async_client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
        )
        return res.choices[0].message.content or ""
