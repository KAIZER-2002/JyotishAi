import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SECRET_KEY", "test-secret-key")

# Mock swisseph for test collection / imports
import types
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

from app.api.v1.routes.chat import get_chat_session_service, router
from app.schemas.chat import ChatResponse, LLMUsageSchema
from app.exceptions.llm import LLMException, ProviderException
from app.services.conversation_service import ConversationNotFoundException
from app.api.deps import get_current_user
from app.db.models.user import User


@pytest.fixture
def mock_chat_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(mock_chat_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_chat_session_service] = lambda: mock_chat_service
    
    mock_user = User(id=uuid4(), email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def valid_chat_request(conversation_id: str = None) -> dict:
    req = {
        "user_query": "What are my career yogas?",
        "birth_data": {
            "date": "1995-06-15T08:30:00Z",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "timezone": "Asia/Kolkata",
            "ayanamsa": "Lahiri",
            "house_system": 1,
        },
    }
    if conversation_id:
        req["conversation_id"] = conversation_id
    return req


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


def test_chat_endpoint_success_new_conversation(
    client: TestClient, mock_chat_service: MagicMock
) -> None:
    # ChatSessionService returns ChatResponse directly now
    convo_id = uuid4()
    mock_usage = LLMUsageSchema(prompt_tokens=150, completion_tokens=250, total_tokens=400)
    mock_response = ChatResponse(
        response="You have a strong career potential supported by Raj Yoga.",
        provider="gemini",
        model="gemini-2.5-flash",
        finish_reason="stop",
        usage=mock_usage,
        conversation_id=convo_id,
    )

    mock_chat_service.chat = AsyncMock(return_value=mock_response)

    response = client.post("/chat", json=valid_chat_request())

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["response"] == "You have a strong career potential supported by Raj Yoga."
    assert data["provider"] == "gemini"
    assert data["model"] == "gemini-2.5-flash"
    assert data["finish_reason"] == "stop"
    assert data["usage"]["prompt_tokens"] == 150
    assert data["usage"]["completion_tokens"] == 250
    assert data["usage"]["total_tokens"] == 400
    assert data["conversation_id"] == str(convo_id)

    # Verify call parameters
    mock_chat_service.chat.assert_called_once()
    called_args, called_kwargs = mock_chat_service.chat.call_args
    assert called_kwargs.get("conversation_id") is None


def test_chat_endpoint_success_existing_conversation(
    client: TestClient, mock_chat_service: MagicMock
) -> None:
    convo_id = uuid4()
    mock_response = ChatResponse(
        response="Following up on your career.",
        provider="gemini",
        model="gemini-2.5-flash",
        finish_reason="stop",
        conversation_id=convo_id,
    )

    mock_chat_service.chat = AsyncMock(return_value=mock_response)

    response = client.post("/chat", json=valid_chat_request(conversation_id=str(convo_id)))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["response"] == "Following up on your career."
    assert data["conversation_id"] == str(convo_id)

    # Verify call parameters passed conversation_id
    mock_chat_service.chat.assert_called_once()
    called_args, called_kwargs = mock_chat_service.chat.call_args
    assert called_kwargs.get("conversation_id") == convo_id


def test_chat_endpoint_conversation_not_found(
    client: TestClient, mock_chat_service: MagicMock
) -> None:
    mock_chat_service.chat = AsyncMock(
        side_effect=ConversationNotFoundException("Conversation not found")
    )

    response = client.post("/chat", json=valid_chat_request(conversation_id=str(uuid4())))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Conversation not found" in response.json()["detail"]


def test_chat_endpoint_empty_query(client: TestClient) -> None:
    payload = valid_chat_request()
    payload["user_query"] = "    "

    response = client.post("/chat", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "user_query cannot be empty" in response.json()["detail"]


def test_chat_endpoint_validation_error_birth_data(client: TestClient) -> None:
    payload = valid_chat_request()
    payload["birth_data"]["latitude"] = 150.0

    response = client.post("/chat", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_chat_endpoint_provider_exception(
    client: TestClient, mock_chat_service: MagicMock
) -> None:
    mock_chat_service.chat = AsyncMock(
        side_effect=ProviderException("Invalid API Key provided")
    )

    response = client.post("/chat", json=valid_chat_request())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "LLM Provider Error" in response.json()["detail"]


def test_chat_endpoint_unexpected_exception(
    client: TestClient, mock_chat_service: MagicMock
) -> None:
    mock_chat_service.chat = AsyncMock(side_effect=ValueError("swiss ephemeris error"))

    response = client.post("/chat", json=valid_chat_request())

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "unexpected error" in response.json()["detail"]


def test_chat_endpoint_dependency_injection(
    client: TestClient, mock_chat_service: MagicMock
) -> None:
    mock_response = ChatResponse(
        response="OK",
        provider="test",
        model="test",
        finish_reason="stop",
        conversation_id=uuid4(),
    )
    mock_chat_service.chat = AsyncMock(return_value=mock_response)

    response = client.post("/chat", json=valid_chat_request())
    assert response.status_code == status.HTTP_200_OK

    mock_chat_service.chat.assert_called_once()
