import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.db.models import User, Conversation, Message
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.services.conversation_service import (
    ConversationService,
    ConversationNotFoundException,
    ConversationServiceException,
)

# In-memory SQLite for async tests
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


# Helper to create a dummy user in database
async def create_dummy_user(db: AsyncSession) -> User:
    user = User(
        email="test_persist@example.com",
        username="test_persist_user",
        hashed_password="somehashedpwd",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Repository Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conversation_repository_crud(db_session: AsyncSession) -> None:
    user = await create_dummy_user(db_session)
    repo = ConversationRepository(db_session)

    # 1. Create
    conv = await repo.create(user_id=user.id, title="Test Chat")
    assert conv.id is not None
    assert conv.title == "Test Chat"
    assert conv.user_id == user.id

    # 2. Read
    fetched = await repo.get_by_id(conv.id)
    assert fetched is not None
    assert fetched.id == conv.id
    assert fetched.title == "Test Chat"

    # 3. Update Title
    updated = await repo.update_title(conv.id, "Updated Chat Title")
    assert updated is not None
    assert updated.title == "Updated Chat Title"

    # Verify change persisted
    fetched_updated = await repo.get_by_id(conv.id)
    assert fetched_updated.title == "Updated Chat Title"

    # 4. Delete
    deleted = await repo.delete(conv.id)
    assert deleted is True

    # Verify not found
    fetched_deleted = await repo.get_by_id(conv.id)
    assert fetched_deleted is None

    # Delete non-existent
    deleted_nonexistent = await repo.delete(uuid4())
    assert deleted_nonexistent is False


@pytest.mark.asyncio
async def test_message_repository_crud(db_session: AsyncSession) -> None:
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)

    conv = await conv_repo.create(title="Message Test")

    # Create message
    msg = await msg_repo.create(
        conversation_id=conv.id,
        role="user",
        content="Hello world",
    )
    assert msg.id is not None
    assert msg.conversation_id == conv.id
    assert msg.role == "user"
    assert msg.content == "Hello world"

    # Get by ID
    fetched_msg = await msg_repo.get_by_id(msg.id)
    assert fetched_msg is not None
    assert fetched_msg.content == "Hello world"

    # List by conversation
    messages = await msg_repo.list_by_conversation(conv.id)
    assert len(messages) == 1
    assert messages[0].id == msg.id


# ---------------------------------------------------------------------------
# Cascade Delete Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conversation_cascade_delete(db_session: AsyncSession) -> None:
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)

    # Create conversation and messages
    conv = await conv_repo.create(title="Cascade Test")
    msg1 = await msg_repo.create(conv.id, "user", "Msg 1")
    msg2 = await msg_repo.create(conv.id, "model", "Msg 2")

    # Verify messages exist
    messages_before = await msg_repo.list_by_conversation(conv.id)
    assert len(messages_before) == 2

    # Delete conversation
    await conv_repo.delete(conv.id)

    # Verify messages are cascade deleted
    msg1_after = await msg_repo.get_by_id(msg1.id)
    msg2_after = await msg_repo.get_by_id(msg2.id)
    assert msg1_after is None
    assert msg2_after is None


# ---------------------------------------------------------------------------
# Pagination Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conversation_pagination(db_session: AsyncSession) -> None:
    user = await create_dummy_user(db_session)
    repo = ConversationRepository(db_session)

    # Create multiple conversations
    convs = []
    for i in range(5):
        conv = await repo.create(user_id=user.id, title=f"Chat {i}")
        convs.append(conv)

    # List page 1 (limit 2)
    page_1 = await repo.list_by_user(user_id=user.id, limit=2, offset=0)
    assert len(page_1) == 2

    # List page 2 (limit 2, offset 2)
    page_2 = await repo.list_by_user(user_id=user.id, limit=2, offset=2)
    assert len(page_2) == 2

    # List page 3 (limit 2, offset 4)
    page_3 = await repo.list_by_user(user_id=user.id, limit=2, offset=4)
    assert len(page_3) == 1

    # Ensure no overlaps
    p1_ids = {c.id for c in page_1}
    p2_ids = {c.id for c in page_2}
    p3_ids = {c.id for c in page_3}
    assert p1_ids.isdisjoint(p2_ids)
    assert p2_ids.isdisjoint(p3_ids)


# ---------------------------------------------------------------------------
# Service-Level Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conversation_service_flows(db_session: AsyncSession) -> None:
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    service = ConversationService(conv_repo, msg_repo)

    user = await create_dummy_user(db_session)

    # Create conversation
    conv = await service.create_conversation(user_id=user.id, title="Service Chat")
    assert conv.title == "Service Chat"

    # Create default title conversation
    conv_default = await service.create_conversation(user_id=user.id)
    assert conv_default.title == "New Conversation"

    # Get conversation (loaded with empty messages)
    fetched = await service.get_conversation(conv.id)
    assert fetched.id == conv.id
    assert len(fetched.messages) == 0

    # Append message
    msg = await service.append_message(conv.id, "user", "Tell me about my career.")
    assert msg.role == "user"
    assert msg.content == "Tell me about my career."

    # Verify message appended
    await db_session.refresh(fetched, ["messages"])
    assert len(fetched.messages) == 1
    assert fetched.messages[0].content == "Tell me about my career."

    # Rename conversation
    renamed = await service.rename_conversation(conv.id, "Career Discussion")
    assert renamed.title == "Career Discussion"

    # List conversations
    convs = await service.list_conversations(user_id=user.id)
    # Both conv and conv_default should be listed
    assert len(convs) == 2

    # Delete conversation
    success = await service.delete_conversation(conv.id)
    assert success is True

    # Expect Exception on subsequent get
    with pytest.raises(ConversationNotFoundException):
        await service.get_conversation(conv.id)


@pytest.mark.asyncio
async def test_conversation_service_validation_errors(db_session: AsyncSession) -> None:
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    service = ConversationService(conv_repo, msg_repo)

    # 1. Non-existent conversation operations
    fake_id = uuid4()
    with pytest.raises(ConversationNotFoundException):
        await service.get_conversation(fake_id)

    with pytest.raises(ConversationNotFoundException):
        await service.rename_conversation(fake_id, "New Title")

    with pytest.raises(ConversationNotFoundException):
        await service.delete_conversation(fake_id)

    with pytest.raises(ConversationNotFoundException):
        await service.append_message(fake_id, "user", "hello")

    # 2. Validation constraints
    conv = await service.create_conversation()

    # Empty rename
    with pytest.raises(ConversationServiceException):
        await service.rename_conversation(conv.id, "   ")

    # Empty message role
    with pytest.raises(ConversationServiceException):
        await service.append_message(conv.id, "   ", "content")

    # Empty message content
    with pytest.raises(ConversationServiceException):
        await service.append_message(conv.id, "user", "   ")
