import time
from typing import AsyncGenerator, Optional, Any
from anthropic import Anthropic, AsyncAnthropic

from app.core.config import settings
from app.domain.llm_provider import FinishReason, LLMProvider, LLMRequest, LLMResponse, LLMUsage
from app.domain.prompt import PromptRole
from app.exceptions.llm import ProviderException
from app.services.llm.base import BaseLLMProvider
from app.services.llm.registry import provider_registry


class AnthropicProviderException(ProviderException):
    """Exception raised by AnthropicProvider."""
    pass


def map_anthropic_finish_reason(reason: Optional[str]) -> FinishReason:
    if not reason:
        return FinishReason.UNKNOWN
    r = reason.lower()
    if r == "end_turn":
        return FinishReason.STOP
    if r in ("max_tokens", "length"):
        return FinishReason.LENGTH
    if "refusal" in r or "content" in r:
        return FinishReason.CONTENT_FILTER
    return FinishReason.UNKNOWN


@provider_registry.register("anthropic")
class AnthropicProvider(LLMProvider, BaseLLMProvider):
    """Anthropic LLM Provider supporting Claude models (Sonnet, Haiku, Opus)."""

    def __init__(self) -> None:
        if not settings.ANTHROPIC_API_KEY:
            raise AnthropicProviderException("Configuration error: ANTHROPIC_API_KEY is missing.")
        self._sync_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._async_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _prepare_messages(self, request: LLMRequest):
        system_instruction = None
        messages = []
        if request.prompt and hasattr(request.prompt, "messages"):
            for m in request.prompt.messages:
                if m.role == PromptRole.SYSTEM:
                    system_instruction = m.content
                else:
                    role = "user" if m.role == PromptRole.USER else "assistant"
                    messages.append({"role": role, "content": m.content})
        return system_instruction, messages

    def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model_hint or "claude-3-5-sonnet-20241022"
        system_instruction, messages = self._prepare_messages(request)
        start_time = time.perf_counter()
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": request.max_tokens or 2048,
                "temperature": request.temperature or 0.7,
            }
            if system_instruction:
                kwargs["system"] = system_instruction

            res = self._sync_client.messages.create(**kwargs)
            latency = int((time.perf_counter() - start_time) * 1000)
            text = "".join(b.text for b in res.content if hasattr(b, "text"))
            usage = LLMUsage(
                prompt_tokens=res.usage.input_tokens if res.usage else 0,
                completion_tokens=res.usage.output_tokens if res.usage else 0,
                total_tokens=(res.usage.input_tokens + res.usage.output_tokens) if res.usage else 0,
            )
            return LLMResponse(
                text=text,
                finish_reason=map_anthropic_finish_reason(res.stop_reason),
                usage=usage,
                raw_response=res.model_dump(),
                model=model,
                latency_ms=latency,
            )
        except Exception as e:
            raise AnthropicProviderException(f"Anthropic API error: {str(e)}") from e

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        model = request.model_hint or "claude-3-5-sonnet-20241022"
        system_instruction, messages = self._prepare_messages(request)
        start_time = time.perf_counter()
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": request.max_tokens or 2048,
                "temperature": request.temperature or 0.7,
            }
            if system_instruction:
                kwargs["system"] = system_instruction

            res = await self._async_client.messages.create(**kwargs)
            latency = int((time.perf_counter() - start_time) * 1000)
            text = "".join(b.text for b in res.content if hasattr(b, "text"))
            usage = LLMUsage(
                prompt_tokens=res.usage.input_tokens if res.usage else 0,
                completion_tokens=res.usage.output_tokens if res.usage else 0,
                total_tokens=(res.usage.input_tokens + res.usage.output_tokens) if res.usage else 0,
            )
            return LLMResponse(
                text=text,
                finish_reason=map_anthropic_finish_reason(res.stop_reason),
                usage=usage,
                raw_response=res.model_dump(),
                model=model,
                latency_ms=latency,
            )
        except Exception as e:
            raise AnthropicProviderException(f"Anthropic API error: {str(e)}") from e

    async def astream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        model = request.model_hint or "claude-3-5-sonnet-20241022"
        system_instruction, messages = self._prepare_messages(request)
        start_time = time.perf_counter()
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": request.max_tokens or 2048,
                "temperature": request.temperature or 0.7,
            }
            if system_instruction:
                kwargs["system"] = system_instruction

            async with self._async_client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    latency = int((time.perf_counter() - start_time) * 1000)
                    yield LLMResponse(
                        text=text,
                        finish_reason=FinishReason.STOP,
                        model=model,
                        latency_ms=latency,
                    )
        except Exception as e:
            raise AnthropicProviderException(f"Anthropic Streaming error: {str(e)}") from e

    async def generate(self, *, message: str, model: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        messages = [{"role": "user", "content": message}]
        req_kwargs = {
            "model": model or "claude-3-5-sonnet-20241022",
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        if system_prompt:
            req_kwargs["system"] = system_prompt
        res = await self._async_client.messages.create(**req_kwargs)
        return "".join(b.text for b in res.content if hasattr(b, "text"))
