from typing import Optional, AsyncGenerator
from uuid import UUID
from app.schemas.astrology import BirthChartRequest
from app.schemas.chat import ChatResponse, LLMUsageSchema
from app.services.conversation_service import ConversationService
from app.services.astrology.astrology_chat_service import AstrologyChatService
from app.domain.llm_provider import LLMResponse


class ChatSessionService:
    """
    Orchestration service responsible for stateful, persistent chat conversations.
    """

    def __init__(
        self,
        conversation_service: ConversationService,
        astrology_chat_service: AstrologyChatService,
    ) -> None:
        self._conversation_service = conversation_service
        self._astrology_chat_service = astrology_chat_service

    async def chat(
        self,
        birth_data: BirthChartRequest,
        user_query: str,
        conversation_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        model_hint: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """
        Coordinates a single chat turn in a persistent conversation.
        """
        if not user_query.strip():
            raise ValueError("user_query cannot be empty.")

        # 1. Create conversation if not present
        if conversation_id is None:
            # Generate a title from the user query
            words = user_query.split()
            title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
            conversation = await self._conversation_service.create_conversation(
                user_id=user_id,
                title=title,
            )
            conversation_id = conversation.id
            history = []
        else:
            # 2. Load conversation history
            # If the conversation does not exist, get_conversation raises ConversationNotFoundException
            conversation = await self._conversation_service.get_conversation(conversation_id)
            history = list(conversation.messages)

        # 3. Append user message
        await self._conversation_service.append_message(
            conversation_id=conversation_id,
            role="user",
            content=user_query,
        )

        try:
            # 4. Invoke AstrologyChatService with conversation history
            response = await self._astrology_chat_service.chat(
                birth_data=birth_data,
                user_query=user_query,
                history=history,
                model_hint=model_hint,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 5. Append assistant response
            await self._conversation_service.append_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response.text,
            )

            # 6. Format and return ChatResponse
            usage = None
            if response.usage:
                usage = LLMUsageSchema(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

            return ChatResponse(
                response=response.text,
                provider=response.provider,
                model=response.model,
                finish_reason=response.finish_reason.value,
                usage=usage,
                conversation_id=conversation_id,
            )

        except Exception as e:
            # Propagating exceptions so the API layer can handle them appropriately
            raise

    async def stream_chat(
        self,
        birth_data: BirthChartRequest,
        user_query: str,
        conversation_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        model_hint: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        conversation_id_out: Optional[list] = None,
    ) -> AsyncGenerator[LLMResponse, None]:
        """
        Streaming variant of chat().

        1. Creates/loads the conversation.
        2. Persists the user message.
        3. Streams LLM chunks — each is yielded immediately.
        4. After the stream is exhausted, assembles the full text and persists the
           assistant message, preserving transactional correctness.
        """
        if not user_query.strip():
            raise ValueError("user_query cannot be empty.")

        # 1. Create or load conversation
        if conversation_id is None:
            words = user_query.split()
            title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
            conversation = await self._conversation_service.create_conversation(
                user_id=user_id,
                title=title,
            )
            conversation_id = conversation.id
            if conversation_id_out is not None:
                conversation_id_out.append(conversation_id)
            history = []
        else:
            if conversation_id_out is not None:
                conversation_id_out.append(conversation_id)
            conversation = await self._conversation_service.get_conversation(conversation_id)
            history = list(conversation.messages)

        # 2. Persist user message before streaming
        await self._conversation_service.append_message(
            conversation_id=conversation_id,
            role="user",
            content=user_query,
        )

        # 3. Stream chunks from AstrologyChatService
        collected_text: list[str] = []
        last_chunk: LLMResponse | None = None

        async for chunk in self._astrology_chat_service.stream_chat(
            birth_data=birth_data,
            user_query=user_query,
            history=history,
            model_hint=model_hint,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            collected_text.append(chunk.text)
            last_chunk = chunk
            yield chunk

        # 4. Persist the fully assembled assistant reply
        full_text = "".join(collected_text)
        if full_text:
            await self._conversation_service.append_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_text,
            )
