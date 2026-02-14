from logger import configure_logging
from models.intent import Intent
from schemas.intent_schema import IntentCreate
from typing import Optional, Tuple, Union, Dict, List, Any
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import asc, desc, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = configure_logging(__name__)


class IntentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_intent(self, intent_data: IntentCreate) -> Optional[Intent]:
        new_intent = Intent(**intent_data.model_dump())
        try:
            self.db.add(new_intent)
            self.db.commit()
            self.db.refresh(new_intent)
            return new_intent
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy IntegrityError: {e}")
            raise HTTPException(
                status_code=409,
                detail="Intent with same intent class name already exists. Please check and retry.",
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy Error: {e}")
            return None

    def update_intent(self, update_data: dict) -> Optional[Intent]:
        identifier = update_data.get("intent_uuid")
        query_filter = (
            Intent.id == identifier
            if isinstance(identifier, UUID)
            else Intent.intent_class == identifier
        )
        intent = self.db.query(Intent).filter(query_filter).first()
        if not intent:
            return None
        try:
            for key, value in update_data.items():
                if hasattr(intent, key) and key != "intent_uuid":
                    setattr(intent, key, value)
            self.db.commit()
            self.db.refresh(intent)
            return intent
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy IntegrityError: {e}")
            raise HTTPException(
                status_code=409,
                detail="Intent with same intent class name already exists. Please check and retry.",
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"SQLAlchemy Error: {e}")
            return None

    def get_intent(self, identifier: Union[UUID, str]) -> Optional[Intent]:
        if isinstance(identifier, UUID):
            query_filter = Intent.id == identifier
        elif isinstance(identifier, str):
            query_filter = Intent.intent_class == identifier
        else:
            raise ValueError("Identifier must be a UUID or a intent_class string")
        try:
            return self.db.query(Intent).filter(query_filter).first()
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            return None

    def get_all_intents(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Intent], int]:
        query = self.db.query(Intent)

        if filters:
            for key, values in filters.items():
                if hasattr(Intent, key):
                    if isinstance(values, list):
                        condition = or_(
                            *(getattr(Intent, key) == value for value in values)
                        )
                        query = query.filter(condition)
                    else:
                        query = query.filter(getattr(Intent, key) == values)

        if hasattr(Intent, sort_by):
            order = (
                asc(getattr(Intent, sort_by))
                if sort_order == "asc"
                else desc(getattr(Intent, sort_by))
            )
            query = query.order_by(order)

        try:
            total = query.count()

            if page and page_size:
                skip = (page - 1) * page_size
                intents = query.offset(skip).limit(page_size).all()
            else:
                intents = query.all()

            return intents, total
        
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            return [], 0

    def search_intent(
        self,
        keyword: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Intent], int]:
        query = self.db.query(Intent)

        if filters:
            for key, values in filters.items():
                if hasattr(Intent, key):
                    if isinstance(values, list):
                        condition = or_(
                            *(getattr(Intent, key) == value for value in values)
                        )
                        query = query.filter(condition)
                    else:
                        query = query.filter(getattr(Intent, key) == values)

        if keyword:
            query = query.filter(
                or_(
                    Intent.name.ilike(f"%{keyword}%"),
                    Intent.description.ilike(f"%{keyword}%"),
                    Intent.intent_class.ilike(f"%{keyword}%"),
                )
            )

        if hasattr(Intent, sort_by):
            order = (
                asc(getattr(Intent, sort_by))
                if sort_order == "asc"
                else desc(getattr(Intent, sort_by))
            )
            query = query.order_by(order)

        try:
            total = query.count()

            if page and page_size:
                skip = (page - 1) * page_size
                intents = query.offset(skip).limit(page_size).all()
            else:
                intents = query.all()

            return intents, total
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            return [], 0

    def delete_intent(self, identifier: Union[UUID, str]) -> Optional[bool]:
        query_filter = (
            Intent.id == identifier
            if isinstance(identifier, UUID)
            else Intent.intent_class == identifier
        )
        intent = self.db.query(Intent).filter(query_filter).first()
        if not intent:
            return False
        try:
            self.db.delete(intent)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error: {e}")
            self.db.rollback()
            return False