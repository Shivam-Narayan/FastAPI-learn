"""
backend/models/event_inbox.py - EventInbox Model for integration framework

Intermediate event storage before agent routing. Deduplication ensures single
processing per external event.
"""

from db_pool import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid


class EventInbox(Base):
    """Represents an ingested event waiting to be processed by an agent.

    Events flow: External System → Adapter → EventInbox → Agent Worker → Task
    """
    __tablename__ = "event_inbox"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign Keys
    task_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event Identity
    external_event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Provider-native event ID (e.g., Graph message ID, S3 ETag)",
    )

    dedupe_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Unique key for deduplication (e.g., task_source_id:external_event_id)",
    )

    # Event Data
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Normalized event payload (what the agent processes)",
    )

    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        comment="Processing context: trace_ids, attempts_history, routing, ingestion_stats",
    )

    # Processing Status
    status: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {"state": "pending", "attempts": 0},
        nullable=False,
        comment="Processing progress: state, attempts, last_attempt_at, errors, progress, worker_id",
    )

    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the event was successfully processed",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last error message (deprecated - use status.last_error instead)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    # Relationships
    task_source: Mapped["TaskSource"] = relationship(
        "TaskSource",
        back_populates="events",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('dedupe_key', name='uq_event_inbox_dedupe_key'),
    )

    def __repr__(self) -> str:
        state = self.status.get("state", "unknown") if isinstance(self.status, dict) else "unknown"
        return f"<EventInbox(id={self.id}, dedupe_key='{self.dedupe_key}', state='{state}')>"
