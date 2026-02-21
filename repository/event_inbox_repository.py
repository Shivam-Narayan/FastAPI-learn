from logger import configure_logging
from models.event_inbox import EventInbox

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import asc, desc, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = configure_logging(__name__)


class EventInboxRepository:
    def __init__(self, db: Session):
        self.db = db

    def insert_event(self, data: dict) -> Optional[EventInbox]:
        evt = EventInbox(**data)
        try:
            self.db.add(evt)
            self.db.commit()
            self.db.refresh(evt)
            return evt
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Deduplication conflict: {e}")
            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy Error: {e}")
            return None

    def get_pending(self, limit: int = 100) -> List[EventInbox]:
        try:
            return (
                self.db.query(EventInbox)
                .filter(EventInbox.status['state'].astext == 'pending')
                .order_by(EventInbox.created_at)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            return []

    def mark_processed(self, event_id: UUID) -> bool:
        evt = self.db.query(EventInbox).filter(EventInbox.id == event_id).first()
        if not evt:
            return False
        try:
            evt.status = {'state': 'processed', 'attempts': evt.status.get('attempts', 0) + 1}
            evt.processed_at = func.now()
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            self.db.rollback()
            return False

    def update_status(self, event_id: UUID, status_update: dict) -> bool:
        evt = self.db.query(EventInbox).filter(EventInbox.id == event_id).first()
        if not evt:
            return False
        try:
            evt.status.update(status_update)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            self.db.rollback()
            return False
