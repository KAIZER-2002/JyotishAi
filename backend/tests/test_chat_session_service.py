import os
import sys
import types

os.environ.setdefault("SECRET_KEY", "test-secret-key")

sys.modules.setdefault(
    "swisseph",
    types.SimpleNamespace(
        houses=types.SimpleNamespace(P_PLACIDUS=1),
        FLG_SWIEPH=2,
        FLG_MOSEPH=4,
        FLG_SIDEREAL=65536,
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
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService, ConversationNotFoundException
from app.services.chat_session_service import ChatSessionService
from app.services.astrology.astrology_chat_service import AstrologyChatService
from app.schemas.astrology import BirthChartRequest
from app.domain.llm_provider import LLMResponse, LLMUsage, FinishReason
from app.exceptions.llm import ProviderException

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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
def birth_chart_request() -> BirthChartRequest:
    return BirthChartRequest(
        date="1995-06-15T08:30:00Z",
        latitude=13.0827,
        longitude=80.2707,
        timezone="Asia/Kolkata",
        ayanamsa="Lahiri",
        house_system=1,
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_session_new_conversation(
    db_session: AsyncSession, birth_chart_request: BirthChartRequest
) -> None:
    # 1. Setup real persistence components
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)

    # 2. Setup mock AstrologyChatService
    mock_astrology_chat_service = AsyncMock(spec=AstrologyChatService)
    mock_usage = LLMUsage(prompt_tokens=100, completion_tokens=150, total_tokens=250)
    mock_llm_response = LLMResponse(
        text="This is the AI response.",
        finish_reason=FinishReason.STOP,
        usage=mock_usage,
        model="gemini-2.5-flash",
        provider="gemini",
    )
    mock_astrology_chat_service.chat.return_value = mock_llm_response

    # 3. Instantiate ChatSessionService
    session_service = ChatSessionService(conv_service, mock_astrology_chat_service)

    # 4. Invoke chat with NO conversation_id
    response = await session_service.chat(
        birth_data=birth_chart_request,
        user_query="My query for new convo",
    )

    # 5. Assert response schema mapping
    assert response.conversation_id is not None
    assert response.response == "This is the AI response."
    assert response.provider == "gemini"
    assert response.model == "gemini-2.5-flash"
    assert response.finish_reason == "stop"
    assert response.usage.total_tokens == 250

    # 6. Verify messages were persisted in the database
    # Clear the session cache to fetch from DB
    db_session.expire_all()
    conv = await conv_service.get_conversation(response.conversation_id)
    assert len(conv.messages) == 2
    assert conv.messages[0].role == "user"
    assert conv.messages[0].content == "My query for new convo"
    assert conv.messages[1].role == "assistant"
    assert conv.messages[1].content == "This is the AI response."

    # Verify AstrologyChatService was invoked with history = []
    mock_astrology_chat_service.chat.assert_called_once_with(
        birth_data=birth_chart_request,
        user_query="My query for new convo",
        history=[],
        model_hint=None,
        temperature=None,
        max_tokens=None,
    )


@pytest.mark.asyncio
async def test_chat_session_existing_conversation(
    db_session: AsyncSession, birth_chart_request: BirthChartRequest
) -> None:
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)

    # Create a pre-existing conversation with one round of history
    conv = await conv_service.create_conversation(title="Existing convo")
    await conv_service.append_message(conv.id, "user", "First question")
    await conv_service.append_message(conv.id, "assistant", "First answer")
    # Refresh conversation relationship before calling the session service
    await db_session.refresh(conv, ["messages"])

    mock_astrology_chat_service = AsyncMock(spec=AstrologyChatService)
    mock_llm_response = LLMResponse(
        text="Second answer",
        finish_reason=FinishReason.STOP,
        model="gemini-2.5-flash",
        provider="gemini",
    )
    mock_astrology_chat_service.chat.return_value = mock_llm_response

    session_service = ChatSessionService(conv_service, mock_astrology_chat_service)

    # Invoke chat turns on existing conversation
    response = await session_service.chat(
        birth_data=birth_chart_request,
        user_query="Second question",
        conversation_id=conv.id,
    )

    assert response.conversation_id == conv.id
    assert response.response == "Second answer"

    # Verify history loading and passing to AI service
    # The history passed to AstrologyChatService should only contain the messages PRIOR to the new query
    mock_astrology_chat_service.chat.assert_called_once()
    called_args, called_kwargs = mock_astrology_chat_service.chat.call_args
    passed_history = called_kwargs.get("history")
    
    assert passed_history is not None
    assert len(passed_history) == 2
    assert passed_history[0].content == "First question"
    assert passed_history[1].content == "First answer"

    # Verify database now contains all 4 messages (2 old + 2 new)
    updated_conv = await conv_service.get_conversation(conv.id)
    await db_session.refresh(updated_conv, ["messages"])
    assert len(updated_conv.messages) == 4
    assert updated_conv.messages[2].content == "Second question"
    assert updated_conv.messages[3].content == "Second answer"


@pytest.mark.asyncio
async def test_chat_session_not_found(
    db_session: AsyncSession, birth_chart_request: BirthChartRequest
) -> None:
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)
    mock_astrology_chat_service = AsyncMock(spec=AstrologyChatService)

    session_service = ChatSessionService(conv_service, mock_astrology_chat_service)

    fake_id = uuid4()
    with pytest.raises(ConversationNotFoundException):
        await session_service.chat(
            birth_data=birth_chart_request,
            user_query="Hello",
            conversation_id=fake_id,
        )


@pytest.mark.asyncio
async def test_chat_session_provider_exception(
    db_session: AsyncSession, birth_chart_request: BirthChartRequest
) -> None:
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    conv_service = ConversationService(conv_repo, msg_repo)

    mock_astrology_chat_service = AsyncMock(spec=AstrologyChatService)
    # Mock LLM provider raising exception
    mock_astrology_chat_service.chat.side_effect = ProviderException("API Key Error")

    session_service = ChatSessionService(conv_service, mock_astrology_chat_service)

    # We expect the provider exception to propagate
    with pytest.raises(ProviderException):
        await session_service.chat(
            birth_data=birth_chart_request,
            user_query="Should fail generation",
        )

    # Note: Even though generation failed, the user query should still be persisted
    # Find the newly created conversation since we didn't pass conversation_id
    convs = await conv_service.list_conversations(user_id=None)
    assert len(convs) == 1
    await db_session.refresh(convs[0], ["messages"])
    assert len(convs[0].messages) == 1
    assert convs[0].messages[0].content == "Should fail generation"
