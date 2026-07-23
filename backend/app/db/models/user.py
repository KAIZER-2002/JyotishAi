from datetime import datetime, date, timezone
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, Boolean, Date, Float, JSON, Integer, text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    """
    User model for authentication and profile management.
    """
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False
    )

    # ─── Profile fields ───────────────────────────────────────────────────────

    timezone: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="IANA timezone identifier, e.g. 'Asia/Kolkata'"
    )
    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    time_of_birth: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        comment="HH:MM:SS in local time"
    )
    birth_place: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    ayanamsa: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Preferred ayanamsa, e.g. 'Lahiri'"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="Base64 data URI or URL of the avatar image"
    )
    gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )
    settings: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="User settings and preferences stored as JSON"
    )
    token_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default=text("1"),
        nullable=False,
        comment="Security token version claim used to invalidate all active sessions"
    )

    # ─── Timestamps ───────────────────────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
