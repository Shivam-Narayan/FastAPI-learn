from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db_pool import Base
import uuid


class Intent(Base):
    __tablename__ = "intents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String)
    description = Column(String)
    intent_class = Column(String, unique=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships


"""
We will move away from this in the future, but for now we need to keep it here.
In future we will use class goup feature.
"""
