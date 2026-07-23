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

# Mock swisseph
import types
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

from app.api.v1.routes.documents import router, _build_document_service, get_current_user
from app.db.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentAlreadyExistsException, DocumentNotFoundException


@pytest.fixture
def mock_document_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def dummy_user() -> User:
    return User(
        id=uuid4(),
        email="test_user@jyotish.ai",
        username="test_user",
        is_active=True
    )


@pytest.fixture
def client(mock_document_service: MagicMock, dummy_user: User) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    app.dependency_overrides[_build_document_service] = lambda: mock_document_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_upload_document_success(client: TestClient, mock_document_service: MagicMock, dummy_user: User):
    mock_doc = {
        "id": "1234567890abcdef1234567890abcdef",
        "filename": "chart.pdf",
        "media_type": "application/pdf",
        "size_bytes": 1024,
        "status": "pending",
        "user_id": str(dummy_user.id),
        "created_at": "2026-07-17T19:30:00Z",
        "updated_at": "2026-07-17T19:30:00Z"
    }
    
    mock_document_service.upload_document = AsyncMock(return_value=mock_doc)

    files = {"file": ("chart.pdf", b"pdf content bytes", "application/pdf")}
    response = client.post("/documents/upload", files=files)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == "1234567890abcdef1234567890abcdef"
    assert data["filename"] == "chart.pdf"
    assert data["status"] == "pending"


def test_upload_document_unsupported_format(client: TestClient):
    files = {"file": ("chart.exe", b"executable bytes", "application/octet-stream")}
    response = client.post("/documents/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported file format" in response.json()["detail"]


def test_list_documents(client: TestClient, mock_document_service: MagicMock, dummy_user: User):
    mock_doc = {
        "id": "1234567890abcdef1234567890abcdef",
        "filename": "chart.pdf",
        "media_type": "application/pdf",
        "size_bytes": 1024,
        "status": "completed",
        "user_id": str(dummy_user.id),
        "created_at": "2026-07-17T19:30:00Z",
        "updated_at": "2026-07-17T19:30:00Z"
    }

    mock_document_service.list_documents = AsyncMock(return_value=([mock_doc], 1))

    response = client.get("/documents?skip=0&limit=5")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_count"] == 1
    assert len(data["documents"]) == 1
    assert data["documents"][0]["id"] == "1234567890abcdef1234567890abcdef"


def test_get_document_preview(client: TestClient, mock_document_service: MagicMock, dummy_user: User):
    mock_doc = MagicMock()
    mock_doc.id = "123"
    mock_doc.filename = "chart.txt"
    mock_document_service.get_document = AsyncMock(return_value=mock_doc)
    mock_document_service.get_preview = AsyncMock(return_value="preview content lines")

    response = client.get("/documents/123/preview")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == "123"
    assert data["content_preview"] == "preview content lines"


def test_delete_document_success(client: TestClient, mock_document_service: MagicMock):
    mock_document_service.delete_document = AsyncMock(return_value=True)

    response = client.delete("/documents/123")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""
