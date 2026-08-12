import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SECRET_KEY", "test-secret-key")

# Mock swisseph for imports
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

from app.api.v1.routes.conversations import router, get_conversation_service
from app.api.deps import get_current_user, get_current_user_optional
from app.db.models.user import User
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.services.conversation_service import ConversationNotFoundException


@pytest.fixture
def mock_user() -> User:
    return User(
        id=uuid4(),
        email="test_user@example.com",
        username="testuser",
        is_active=True,
    )


@pytest.fixture
def mock_conversation_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(mock_user: User, mock_conversation_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_user_optional] = lambda: mock_user
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_conversations(client: TestClient, mock_user: User, mock_conversation_service: MagicMock):
    # Setup mock return data
    conv_id = uuid4()
    mock_conv = Conversation(
        id=conv_id,
        title="Test Conversation",
        user_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    mock_conversation_service.list_conversations = AsyncMock(return_value=[mock_conv])

    response = client.get("/conversations?limit=10&offset=0&search=Test")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(conv_id)
    assert data[0]["title"] == "Test Conversation"

    mock_conversation_service.list_conversations.assert_called_once_with(
        user_id=mock_user.id, limit=10, offset=0, search="Test"
    )


def test_get_conversation_details_owner(client: TestClient, mock_user: User, mock_conversation_service: MagicMock):
    conv_id = uuid4()
    mock_conv = Conversation(
        id=conv_id,
        title="Test Conversation Detail",
        user_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_msg = Message(
        id=uuid4(),
        conversation_id=conv_id,
        role="user",
        content="Hello Astrology",
        created_at=datetime.now(timezone.utc),
    )
    mock_conv.messages = [mock_msg]

    mock_conversation_service.get_conversation = AsyncMock(return_value=mock_conv)

    response = client.get(f"/conversations/{conv_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(conv_id)
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "Hello Astrology"


def test_get_conversation_details_not_owner(client: TestClient, mock_user: User, mock_conversation_service: MagicMock):
    conv_id = uuid4()
    other_user_id = uuid4()
    mock_conv = Conversation(
        id=conv_id,
        title="Other User Conversation",
        user_id=other_user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_conversation_service.get_conversation = AsyncMock(return_value=mock_conv)

    response = client.get(f"/conversations/{conv_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Conversation not found."


def test_rename_conversation_owner(client: TestClient, mock_user: User, mock_conversation_service: MagicMock):
    conv_id = uuid4()
    mock_conv = Conversation(
        id=conv_id,
        title="Original Title",
        user_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    updated_conv = Conversation(
        id=conv_id,
        title="Updated Title",
        user_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_conversation_service.get_conversation = AsyncMock(return_value=mock_conv)
    mock_conversation_service.rename_conversation = AsyncMock(return_value=updated_conv)

    response = client.patch(f"/conversations/{conv_id}", json={"title": "Updated Title"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Title"


def test_delete_conversation_owner(client: TestClient, mock_user: User, mock_conversation_service: MagicMock):
    conv_id = uuid4()
    mock_conv = Conversation(
        id=conv_id,
        title="To Delete",
        user_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_conversation_service.get_conversation = AsyncMock(return_value=mock_conv)
    mock_conversation_service.delete_conversation = AsyncMock(return_value=True)

    response = client.delete(f"/conversations/{conv_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_conversation_service.delete_conversation.assert_called_once_with(conv_id)
