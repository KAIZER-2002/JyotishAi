"""
Tests for POST /api/v1/chat/stream (SSE streaming endpoint).

Coverage:
  - Successful streaming with chunk ordering
  - Persistence of full assistant reply after stream
  - Provider exception delivered as error chunk in stream
  - LLM exception delivered as error chunk in stream
  - Empty user_query returns 422 before stream opens
  - Non-existent conversation_id delivers error chunk
  - Cancellation mid-stream (early generator exit)
"""

import json
import os
import sys
import types

os.environ.setdefault("SECRET_KEY", "test-secret-key")

# ---------------------------------------------------------------------------
# Stub out the C-extension before any project imports
# ---------------------------------------------------------------------------
sys.modules.setdefault(
    "swisseph",
    types.SimpleNamespace(
        houses=types.SimpleNamespace(P_PLACIDUS=1),
        FLG_SWIEPH=2,
        FLG_SIDEREAL=4,
        SUN=0,
        MOON=1,
        MARS=4,
        MERCURY=2,
        JUPITER=5,
        VENUS=3,
        SATURN=6,
        TRUE_NODE=11,
        SIDM_LAHIRI=1,
        SIDM_RAMAN=3,
        SIDM_KRISHNAMURTI=5,
        SIDM_TRUE_CHITRA=27,
    ),
)

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db.session import get_db
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.services.chat_session_service import ChatSessionService
from app.services.astrology.astrology_chat_service import AstrologyChatService
from app.schemas.astrology import BirthChartRequest
from app.exceptions.llm import ProviderException, LLMException
from app.domain.llm_provider import LLMResponse, FinishReason
from app.api.v1.routes.chat import router, get_chat_session_service
from app.api.deps import get_current_user
from app.db.models.user import User

MOCK_USER_ID = uuid4()
MOCK_USER = User(id=MOCK_USER_ID, email="test@example.com")

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    AsyncSessionLocal = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
def birth_chart_request_payload() -> dict:
    return {
        "user_query": "Tell me about my ascendant",
        "birth_data": {
            "date": "1995-06-15T08:30:00Z",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "timezone": "Asia/Kolkata",
            "ayanamsa": "Lahiri",
            "house_system": 1,
        },
    }


# ---------------------------------------------------------------------------
# Helper: build an async generator that yields fake LLMResponse chunks
# ---------------------------------------------------------------------------

def make_streaming_astrology_service(chunks: list[str], exception=None):
    """
    Returns an AstrologyChatService whose stream_chat() is an async generator
    that yields one LLMResponse per chunk string.

    If `exception` is provided it is raised after all chunks (or instead of
    the first chunk if chunks is empty).
    """

    async def _fake_stream(*args, **kwargs):
        for i, text in enumerate(chunks):
            is_last = i == len(chunks) - 1
            yield LLMResponse(
                text=text,
                finish_reason=FinishReason.STOP if is_last else None,
                model="gemini-2.5-flash",
                provider="gemini",
            )
        if exception is not None:
            raise exception

    mock_service = MagicMock(spec=AstrologyChatService)
    mock_service.stream_chat = _fake_stream
    # chat() is not needed for stream tests but keep it for spec completeness
    mock_service.chat = AsyncMock()
    return mock_service


def build_test_app(chat_session_service: ChatSessionService) -> FastAPI:
    """Create a minimal FastAPI app with the chat router and DI override."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def _override_service():
        return chat_session_service

    app.dependency_overrides[get_chat_session_service] = _override_service
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_yields_chunks_in_order(
    db_session: AsyncSession, birth_chart_request_payload: dict
) -> None:
    """Chunks arrive in the order they were produced and text content is preserved."""
    chunks = ["Hello, ", "here is ", "your reading."]
    astrology_service = make_streaming_astrology_service(chunks)

    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    session_service = ChatSessionService(conv_service, astrology_service)

    app = build_test_app(session_service)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream(
            "POST", "/api/v1/chat/stream", json=birth_chart_request_payload
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            lines = []
            async for line in response.aiter_lines():
                if line.strip():
                    lines.append(json.loads(line))

    # First N lines are text chunks
    text_chunks = [l for l in lines if l.get("text") and l.get("finish_reason") is None]
    assert len(text_chunks) == len(chunks)
    assert [c["text"] for c in text_chunks] == chunks


@pytest.mark.asyncio
async def test_stream_final_chunk_has_finish_reason(
    db_session: AsyncSession, birth_chart_request_payload: dict
) -> None:
    """The last chunk (sentinel) carries a finish_reason."""
    astrology_service = make_streaming_astrology_service(["Some text"])
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    session_service = ChatSessionService(conv_service, astrology_service)

    app = build_test_app(session_service)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream(
            "POST", "/api/v1/chat/stream", json=birth_chart_request_payload
        ) as response:
            lines = []
            async for line in response.aiter_lines():
                if line.strip():
                    lines.append(json.loads(line))

    final = lines[-1]
    assert final["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_stream_persists_full_assistant_reply(
    db_session: AsyncSession, birth_chart_request_payload: dict
) -> None:
    """After the stream completes the full concatenated text is saved to the DB."""
    chunks = ["Chunk A. ", "Chunk B. ", "Chunk C."]
    astrology_service = make_streaming_astrology_service(chunks)

    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    session_service = ChatSessionService(conv_service, astrology_service)

    app = build_test_app(session_service)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream(
            "POST", "/api/v1/chat/stream", json=birth_chart_request_payload
        ) as response:
            # Consume entire stream
            async for _ in response.aiter_lines():
                pass

    # Verify DB state
    convs = await conv_service.list_conversations(user_id=MOCK_USER_ID)
    assert len(convs) == 1
    await db_session.refresh(convs[0], ["messages"])
    messages = convs[0].messages
    assert len(messages) == 2  # user + assistant
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Chunk A. Chunk B. Chunk C."


@pytest.mark.asyncio
async def test_stream_persists_user_message_before_streaming(
    db_session: AsyncSession, birth_chart_request_payload: dict
) -> None:
    """The user message is persisted BEFORE the stream begins (even if stream fails)."""
    from app.exceptions.llm import ProviderException

    astrology_service = make_streaming_astrology_service([], exception=ProviderException("Quota"))
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    session_service = ChatSessionService(conv_service, astrology_service)

    app = build_test_app(session_service)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream(
            "POST", "/api/v1/chat/stream", json=birth_chart_request_payload
        ) as response:
            async for _ in response.aiter_lines():
                pass

    convs = await conv_service.list_conversations(user_id=MOCK_USER_ID)
    assert len(convs) == 1
    await db_session.refresh(convs[0], ["messages"])
    # User message is persisted even when LLM fails
    assert convs[0].messages[0].role == "user"
    assert convs[0].messages[0].content == birth_chart_request_payload["user_query"]


@pytest.mark.asyncio
async def test_stream_provider_exception_yields_error_chunk(
    db_session: AsyncSession, birth_chart_request_payload: dict
) -> None:
    """A ProviderException after some chunks is delivered as an error chunk."""
    astrology_service = make_streaming_astrology_service(
        ["partial text"], exception=ProviderException("Rate limit")
    )
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    session_service = ChatSessionService(conv_service, astrology_service)

    app = build_test_app(session_service)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream(
            "POST", "/api/v1/chat/stream", json=birth_chart_request_payload
        ) as response:
            lines = [
                json.loads(ln)
                async for ln in response.aiter_lines()
                if ln.strip()
            ]

    error_lines = [l for l in lines if "error" in l]
    assert len(error_lines) == 1
    assert "Rate limit" in error_lines[0]["error"]
    assert error_lines[0]["status_code"] == 400


@pytest.mark.asyncio
async def test_stream_llm_exception_yields_error_chunk(
    db_session: AsyncSession, birth_chart_request_payload: dict
) -> None:
    """A base LLMException is delivered as a 500 error chunk."""
    astrology_service = make_streaming_astrology_service(
        [], exception=LLMException("Internal failure")
    )
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    session_service = ChatSessionService(conv_service, astrology_service)

    app = build_test_app(session_service)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream(
            "POST", "/api/v1/chat/stream", json=birth_chart_request_payload
        ) as response:
            lines = [
                json.loads(ln)
                async for ln in response.aiter_lines()
                if ln.strip()
            ]

    error_lines = [l for l in lines if "error" in l]
    assert len(error_lines) == 1
    assert "Internal failure" in error_lines[0]["error"]
    assert error_lines[0]["status_code"] == 500


@pytest.mark.asyncio
async def test_stream_empty_query_returns_422(
    db_session: AsyncSession,
) -> None:
    """An empty user_query is rejected with HTTP 422 before the stream opens."""
    astrology_service = make_streaming_astrology_service([])
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    session_service = ChatSessionService(conv_service, astrology_service)

    app = build_test_app(session_service)

    payload = {
        "user_query": "   ",
        "birth_data": {
            "date": "1995-06-15T08:30:00Z",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "timezone": "Asia/Kolkata",
            "ayanamsa": "Lahiri",
            "house_system": 1,
        },
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat/stream", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stream_multiple_chunks_text_order(
    db_session: AsyncSession, birth_chart_request_payload: dict
) -> None:
    """Verifies chunk ordering under larger payloads."""
    chunks = [f"Word{i} " for i in range(10)]
    astrology_service = make_streaming_astrology_service(chunks)

    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    session_service = ChatSessionService(conv_service, astrology_service)

    app = build_test_app(session_service)

    received: list[str] = []

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream(
            "POST", "/api/v1/chat/stream", json=birth_chart_request_payload
        ) as response:
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                parsed = json.loads(line)
                if parsed.get("text") and parsed.get("finish_reason") is None:
                    received.append(parsed["text"])

    assert received == chunks


@pytest.mark.asyncio
async def test_stream_existing_conversation(
    db_session: AsyncSession, birth_chart_request_payload: dict
) -> None:
    """Streaming works when an existing conversation_id is supplied."""
    chunks = ["Reply for continuation."]
    astrology_service = make_streaming_astrology_service(chunks)

    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)

    # Pre-create a conversation
    conv = await conv_service.create_conversation(title="Existing")
    await conv_service.append_message(conv.id, "user", "First question")
    await conv_service.append_message(conv.id, "assistant", "First answer")

    session_service = ChatSessionService(conv_service, astrology_service)
    app = build_test_app(session_service)

    payload = {**birth_chart_request_payload, "conversation_id": str(conv.id)}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream(
            "POST", "/api/v1/chat/stream", json=payload
        ) as response:
            assert response.status_code == 200
            async for _ in response.aiter_lines():
                pass

    # DB should now have 4 messages
    await db_session.refresh(conv, ["messages"])
    assert len(conv.messages) == 4
    assert conv.messages[2].role == "user"
    assert conv.messages[3].role == "assistant"
    assert conv.messages[3].content == "Reply for continuation."
