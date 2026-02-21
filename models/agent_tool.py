"""
backend/models/agent_tool.py - AgentTool Model for integration framework

Binds a Tool template to an Agent through a specific Connection.
"""

from db_pool import Base
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid


class AgentTool(Base):
    """Represents a tool (action) that an agent can invoke.

    Examples:
    - Agent can use "outlook.send_email" via "Support Outlook" connection
    - Agent can use "aws_s3.upload_object" via "Finance AWS" connection
    """
    __tablename__ = "agent_tools"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign Keys
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tool Identity
    provider_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Denormalized from connection for efficient queries",
    )

    tool_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="References TOOLS registry (e.g., 'outlook.send_email')",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="agent_tools",
    )

    connection: Mapped["Connection"] = relationship(
        "Connection",
        back_populates="agent_tools",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('agent_id', 'tool_key', name='uq_agent_tool_key'),
    )

    def __repr__(self) -> str:
        return f"<AgentTool(id={self.id}, tool='{self.tool_key}')>"
