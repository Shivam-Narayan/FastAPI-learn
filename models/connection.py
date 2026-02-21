"""
backend/models/connection.py - Connection Model for integration framework

Represents authenticated credentials for an external system. Connections
are shared by TaskSources (triggers) and AgentTools (actions).
"""

from db_pool import Base
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

from backend.registry import ALL_INTEGRATIONS


class Connection(Base):
    """Authenticated connection to an external system.

    Example providers:
    - Microsoft Graph (OAuth client credentials / tokens)
    - Google APIs (OAuth tokens)
    - AWS IAM (role credentials)
    - Salesforce (JWT bearer / OAuth)
    """

    __tablename__ = "connections"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign Keys
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Connection Identity
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    provider_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Validated against ALL_INTEGRATIONS registry at runtime",
    )

    auth_schema_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="References AUTH_SCHEMAS registry (e.g., 'msft.oauth2.app_only')",
    )

    # Credentials (Fernet encrypted)
    encrypted_credentials: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Fernet-encrypted user inputs: client_id, client_secret, api_keys, etc.",
    )

    encrypted_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Fernet-encrypted OAuth tokens: access_token, refresh_token, expires_at",
    )

    # Non-sensitive configuration
    connection_config: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        comment="Provider-specific non-sensitive config: region, tenant_id, instance_url",
    )

    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        comment="Operational context: validation_attempts, error_details, reauth_history",
    )

    # Status & health
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        comment="User-controlled enable/disable toggle",
    )

    auth_status: Mapped[str] = mapped_column(
        String(32),
        default="valid",
        index=True,
        comment="System-managed: valid, expired, invalid, reauth_required",
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Soft delete timestamp for audit trail",
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

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last TaskSource poll or AgentTool invocation",
    )

    last_validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful authentication check",
    )

    # Validation
    @validates("provider_key")
    def validate_provider_key(self, key, value):
        if value not in ALL_INTEGRATIONS:
            raise ValueError(
                f"Invalid provider_key: '{value}'. "
                f"Must be one of: {', '.join(sorted(ALL_INTEGRATIONS.keys()))}"
            )
        return value

    # Relationships
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
    )

    task_sources: Mapped[list["TaskSource"]] = relationship(
        "TaskSource",
        back_populates="connection",
        cascade="all, delete-orphan",
    )

    agent_tools: Mapped[list["AgentTool"]] = relationship(
        "AgentTool",
        back_populates="connection",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Connection(id={self.id}, name='{self.name}', "
            f"provider='{self.provider_key}', status='{self.auth_status}')>"
        )
