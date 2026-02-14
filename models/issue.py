from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db_pool import Base
import uuid

class Issue(Base):
    __tablename__="issues"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    progress = Column(JSON)
    tag_ids = Column(ARRAY(String))
    agent_task_ids = Column(ARRAY(String))
    issue_metadata = Column(JSONB)
    created_by = Column(UUID, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())