from logger import configure_logging
from models.agent_tool import AgentTool

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import asc, desc, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = configure_logging(__name__)


class AgentToolRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_tool(self, data: dict) -> Optional[AgentTool]:
        tool = AgentTool(**data)
        try:
            self.db.add(tool)
            self.db.commit()
            self.db.refresh(tool)
            return tool
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy IntegrityError: {e}")
            raise HTTPException(status_code=409, detail="Constraint violation when creating AgentTool.")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy Error: {e}")
            return None

    def get_by_id(self, tool_id: UUID) -> Optional[AgentTool]:
        try:
            return self.db.query(AgentTool).filter(AgentTool.id == tool_id).first()
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            return None

    def list(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[AgentTool], int]:
        query = self.db.query(AgentTool)
        if filters:
            for key, values in filters.items():
                if hasattr(AgentTool, key):
                    if isinstance(values, list):
                        condition = or_(*(getattr(AgentTool, key) == v for v in values))
                        query = query.filter(condition)
                    else:
                        query = query.filter(getattr(AgentTool, key) == values)
        if hasattr(AgentTool, sort_by):
            order = asc(getattr(AgentTool, sort_by)) if sort_order == "asc" else desc(getattr(AgentTool, sort_by))
            query = query.order_by(order)
        try:
            total = query.count()
            if page and page_size:
                skip = (page - 1) * page_size
                items = query.offset(skip).limit(page_size).all()
            else:
                items = query.all()
            return items, total
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            return [], 0

    def delete_tool(self, tool_id: UUID) -> bool:
        tool = self.db.query(AgentTool).filter(AgentTool.id == tool_id).first()
        if not tool:
            return False
        try:
            self.db.delete(tool)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            self.db.rollback()
            return False
