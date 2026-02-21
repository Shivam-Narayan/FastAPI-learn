from logger import configure_logging
from models.task_source import TaskSource

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import asc, desc, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = configure_logging(__name__)


class TaskSourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_task_source(self, data: dict) -> Optional[TaskSource]:
        ts = TaskSource(**data)
        try:
            self.db.add(ts)
            self.db.commit()
            self.db.refresh(ts)
            return ts
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy IntegrityError: {e}")
            raise HTTPException(status_code=409, detail="Constraint violation when creating TaskSource.")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy Error: {e}")
            return None

    def get_by_id(self, ts_id: UUID) -> Optional[TaskSource]:
        try:
            return self.db.query(TaskSource).filter(TaskSource.id == ts_id, TaskSource.deleted_at.is_(None)).first()
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
    ) -> Tuple[List[TaskSource], int]:
        query = self.db.query(TaskSource)
        if filters:
            for key, values in filters.items():
                if hasattr(TaskSource, key):
                    if isinstance(values, list):
                        condition = or_(*(getattr(TaskSource, key) == v for v in values))
                        query = query.filter(condition)
                    else:
                        query = query.filter(getattr(TaskSource, key) == values)
        if hasattr(TaskSource, sort_by):
            order = asc(getattr(TaskSource, sort_by)) if sort_order == "asc" else desc(getattr(TaskSource, sort_by))
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

    def update(self, ts_id: UUID, data: dict) -> Optional[TaskSource]:
        ts = self.db.query(TaskSource).filter(TaskSource.id == ts_id).first()
        if not ts:
            return None
        try:
            for k, v in data.items():
                if hasattr(ts, k):
                    setattr(ts, k, v)
            self.db.commit()
            self.db.refresh(ts)
            return ts
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy Error: {e}")
            return None

    def soft_delete(self, ts_id: UUID) -> bool:
        ts = self.db.query(TaskSource).filter(TaskSource.id == ts_id).first()
        if not ts:
            return False
        try:
            ts.deleted_at = func.now()
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            self.db.rollback()
            return False
