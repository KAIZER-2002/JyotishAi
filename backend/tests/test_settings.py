import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

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

from app.api.v1.routes.users import router
from app.api.deps import get_current_user
from app.db.models.user import User
from app.services.user_service import UserService


@pytest.fixture
def mock_user() -> User:
    return User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        is_active=True,
        settings={
            "general": {
                "theme": "dark",
                "language": "en",
                "timezone": "Asia/Kolkata",
                "date_format": "YYYY-MM-DD",
                "time_format": "HH:mm"
            }
        }
    )


@pytest.fixture
def mock_user_service() -> MagicMock:
    service = MagicMock(spec=UserService)
    service.get_settings = AsyncMock()
    service.update_settings = AsyncMock()
    service.delete_user = AsyncMock()
    return service


@pytest.fixture
def client(mock_user: User, mock_user_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    
    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # We also override the UserService builder dependency in users.py
    from app.api.v1.routes.users import _build_user_service
    app.dependency_overrides[_build_user_service] = lambda: mock_user_service
    
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_get_settings(client: TestClient, mock_user_service: MagicMock):
    from app.schemas.user import UserSettingsSchema
    mock_user_service.get_settings.return_value = UserSettingsSchema()

    response = client.get("/users/me/settings")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["general"]["theme"] == "dark"
    mock_user_service.get_settings.assert_called_once()


def test_update_settings(client: TestClient, mock_user_service: MagicMock):
    from app.schemas.user import UserSettingsSchema
    mock_user_service.update_settings.return_value = UserSettingsSchema(
        general={"theme": "light", "language": "en", "timezone": "Asia/Kolkata", "date_format": "YYYY-MM-DD", "time_format": "HH:mm"}
    )

    payload = {
        "general": {
            "theme": "light"
        }
    }
    response = client.patch("/users/me/settings", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["general"]["theme"] == "light"
    mock_user_service.update_settings.assert_called_once()


def test_delete_account(client: TestClient, mock_user_service: MagicMock):
    mock_user_service.delete_user.return_value = True

    response = client.delete("/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Account deleted successfully."
    mock_user_service.delete_user.assert_called_once()


def test_logout_all(client: TestClient):
    response = client.post("/users/me/logout-all")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Successfully logged out of all active sessions."
