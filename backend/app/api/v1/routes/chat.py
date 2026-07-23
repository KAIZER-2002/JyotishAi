from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService, ConversationNotFoundException
from app.services.chat_session_service import ChatSessionService
from app.services.astrology.astrology_chat_service import AstrologyChatService
from app.exceptions.llm import LLMException, ProviderException
from app.schemas.chat import ChatRequest, ChatResponse, StreamChunk
from app.api.deps import get_current_user
from app.db.models.user import User

router = APIRouter()


async def get_chat_session_service(db: AsyncSession = Depends(get_db)) -> ChatSessionService:
    """Dependency to provide a ChatSessionService instance."""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    conv_service = ConversationService(conv_repo, msg_repo)
    astrology_chat_service = AstrologyChatService()
    return ChatSessionService(conv_service, astrology_chat_service)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Astrology AI Chat",
    description="Calculates birth charts, identifies yogas, generates a prompt, and streams insights from Gemini with conversation history.",
)
async def chat(
    request: ChatRequest,
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Endpoint to receive Swiss Ephemeris data, run yoga calculations,
    and generate astrological readings from Gemini with persistent chat history.
    """
    if not request.user_query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation Error: user_query cannot be empty.",
        )

    # Resolve optional user preferences
    model_hint = None
    temperature = None
    max_tokens = None
    user_id = None
    if current_user:
        user_id = current_user.id
        if current_user.settings:
            ai_pref = current_user.settings.get("ai") or {}
            model_hint = ai_pref.get("default_ai_model")
            temperature = ai_pref.get("temperature")
            resp_len = ai_pref.get("response_length")
            if resp_len == "short":
                max_tokens = 500
            elif resp_len == "medium":
                max_tokens = 1500
            elif resp_len == "long":
                max_tokens = 4000

    try:
        response = await chat_session_service.chat(
            birth_data=request.birth_data,
            user_query=request.user_query,
            conversation_id=request.conversation_id,
            user_id=user_id,
            model_hint=model_hint,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response

    except ConversationNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ProviderException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LLM Provider Error: {str(e)}",
        )
    except LLMException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM System Error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.post(
    "/chat/stream",
    status_code=status.HTTP_200_OK,
    summary="Astrology AI Chat — SSE Stream",
    description=(
        "Like POST /chat but responds with a text/event-stream body. "
        "Each line is a JSON-encoded StreamChunk. "
        "The final chunk carries a finish_reason and conversation_id."
    ),
)
async def chat_stream(
    request: ChatRequest,
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Streaming astrology chat endpoint.

    Yields newline-delimited JSON (NDJSON) chunks:
      {"text": "...", "finish_reason": null, "conversation_id": "..."}

    The final chunk has finish_reason set to the provider value (e.g. "stop").
    After the stream closes the full assistant reply is persisted.
    """
    if not request.user_query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation Error: user_query cannot be empty.",
        )

    # Resolve optional user preferences
    model_hint = None
    temperature = None
    max_tokens = None
    user_id = None
    if current_user:
        user_id = current_user.id
        if current_user.settings:
            ai_pref = current_user.settings.get("ai") or {}
            model_hint = ai_pref.get("default_ai_model")
            temperature = ai_pref.get("temperature")
            resp_len = ai_pref.get("response_length")
            if resp_len == "short":
                max_tokens = 500
            elif resp_len == "medium":
                max_tokens = 1500
            elif resp_len == "long":
                max_tokens = 4000

    async def event_generator():
        try:
            last_chunk = None
            conv_id = request.conversation_id
            conv_id_out = []

            async for chunk in chat_session_service.stream_chat(
                birth_data=request.birth_data,
                user_query=request.user_query,
                conversation_id=conv_id,
                user_id=user_id,
                model_hint=model_hint,
                temperature=temperature,
                max_tokens=max_tokens,
                conversation_id_out=conv_id_out,
            ):
                last_chunk = chunk
                payload = StreamChunk(
                    text=chunk.text,
                    finish_reason=None,
                    conversation_id=None,  # populated only on final chunk
                )
                yield json.dumps(payload.model_dump()) + "\n"

            # Final chunk with finish reason and conversation_id
            final_conv_id = str(conv_id_out[0]) if conv_id_out else (str(conv_id) if conv_id else None)
            
            if last_chunk is not None:
                final_payload = StreamChunk(
                    text="",
                    finish_reason=last_chunk.finish_reason.value
                    if last_chunk.finish_reason
                    else None,
                    conversation_id=final_conv_id,
                )
                yield json.dumps(final_payload.model_dump()) + "\n"

        except ConversationNotFoundException as e:
            error_chunk = {"error": str(e), "status_code": 404}
            yield json.dumps(error_chunk) + "\n"
        except ProviderException as e:
            error_chunk = {"error": f"LLM Provider Error: {str(e)}", "status_code": 400}
            yield json.dumps(error_chunk) + "\n"
        except LLMException as e:
            error_chunk = {"error": f"LLM System Error: {str(e)}", "status_code": 500}
            yield json.dumps(error_chunk) + "\n"
        except Exception as e:
            error_chunk = {"error": f"An unexpected error occurred: {str(e)}", "status_code": 500}
            yield json.dumps(error_chunk) + "\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
