# Default libraries
from datetime import datetime
from typing import Optional, Dict, Any
from typing_extensions import Annotated
from uuid import UUID

# Installed libraries
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, Field

# Custom libraries
from configs.integrations_v4 import INTEGRATIONS
from configs.auth_schemas_v4 import AUTH_SCHEMAS


class ConnectionBase(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]  
    provider_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]  
    auth_schema_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]  
    encrypted_credentials: str = Field(..., min_length=1)
    encrypted_token: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    connection_metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True
    auth_status: str = Field(default="valid", max_length=32)
    created_by: Optional[UUID] = None

    @field_validator('provider_key')
    @classmethod
    def validate_provider_key(cls, v: str) -> str:
        """Validate provider_key against INTEGRATIONS config."""
        provider_keys = [integration.get("key") for integration in INTEGRATIONS]
        if v not in provider_keys:
            raise ValueError(f"Invalid provider_key. Must be one of: {', '.join(provider_keys)}")
        return v

    @field_validator('auth_schema_key')
    @classmethod
    def validate_auth_schema_key(cls, v: str) -> str:
        """Validate auth_schema_key against AUTH_SCHEMAS config."""
        if v not in AUTH_SCHEMAS:
            available_schemas = ', '.join(AUTH_SCHEMAS.keys())
            raise ValueError(f"Invalid auth_schema_key. Must be one of: {available_schemas}")
        return v


    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ConnectionCreate(ConnectionBase):
    """Schema for creating a new connection."""
    pass


class ConnectionUpdate(BaseModel):
    """Schema for updating a connection (all fields optional)."""
    name: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]] = None
    provider_key: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]] = None  
    auth_schema_key: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]] = None  
    encrypted_credentials: Optional[str] = Field(None, min_length=1)
    encrypted_token: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    connection_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    auth_status: Optional[str] = Field(None, max_length=32)

    @field_validator('provider_key')
    @classmethod
    def validate_provider_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate provider_key if provided."""
        if v is None:
            return v
        provider_keys = [integration.get("key") for integration in INTEGRATIONS]
        if v not in provider_keys:
            raise ValueError(f"Invalid provider_key. Must be one of: {', '.join(provider_keys)}")
        return v

    @field_validator('auth_schema_key')
    @classmethod
    def validate_auth_schema_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate auth_schema_key if provided."""
        if v is None:
            return v
        if v not in AUTH_SCHEMAS:
            available_schemas = ', '.join(AUTH_SCHEMAS.keys())
            raise ValueError(f"Invalid auth_schema_key. Must be one of: {available_schemas}")
        return v

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ConnectionDetail(ConnectionBase):
    """Schema for connection details (includes read-only fields)."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    last_validated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
