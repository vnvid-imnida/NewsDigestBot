"""SQLAlchemy models for News Digest Bot."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """Telegram bot user."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    language_code: Mapped[str] = mapped_column(
        String(10), nullable=False, default="ru"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    topics: Mapped[List["Topic"]] = relationship(
        "Topic", back_populates="user", cascade="all, delete-orphan"
    )
    schedule: Mapped[Optional["Schedule"]] = relationship(
        "Schedule", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    saved_articles: Mapped[List["SavedArticle"]] = relationship(
        "SavedArticle", back_populates="user", cascade="all, delete-orphan"
    )


class Topic(Base):
    """User's topic of interest for news."""
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="topics"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="topics_user_id_name_unique"),
        Index("topics_user_id_idx", "user_id"),
    )


class Schedule(Base):
    """User's schedule for automatic digest delivery"""
    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    times: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Europe/Moscow"
    )
    last_sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="schedule"
    )


class Article(Base):
    """News article from external API (GNews)."""
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    url: Mapped[str] = mapped_column(
        String(2000), nullable=False
    )
    source_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(2000), nullable=True
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    saved_by: Mapped[List["SavedArticle"]] = relationship(
        "SavedArticle", back_populates="article", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("articles_published_at_desc_idx", published_at.desc()),)


class SavedArticle(Base):
    """Article saved by user to their library."""
    __tablename__ = "saved_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE", nullable=False)
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    article: Mapped["Article"] = relationship(
        "Article", back_populates="saved_by"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="saved_articles"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "article_id", name="saved_articles_user_article_unique"
        ),
        Index("saved_articles_user_saved_at_idx", "user_id", saved_at.desc()),
    )
