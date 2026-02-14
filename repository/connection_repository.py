# Custom libraries
from logger import configure_logging
from models.connection import Connection

# Default libraries
from typing import Optional
from uuid import UUID

# Installed libraries
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

# Schema imports
from schemas.connection_schema import ConnectionCreate


logger = configure_logging(__name__)


class ConnectionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_connection(self, connection_data: ConnectionCreate) -> Optional[Connection]:
        connection = Connection(**connection_data.model_dump())
        try:
            self.db.add(connection)
            await self.db.commit()
            await self.db.refresh(connection)
            return connection
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"SQLAlchemy IntegrityError: {e}")
            raise HTTPException(
                status_code=409,
                detail="Connection with same name already exists or constraint violation occurred.",
            )
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"SQLAlchemy Error while creating Connection: {e}")
            return None

    async def get_connection_by_id(self, connection_id: UUID) -> Optional[Connection]:
        try:
            result = await self.db.execute(
                select(Connection).filter(
                    Connection.id == connection_id,
                    Connection.deleted_at.is_(None)
                )
            )
            connection = result.scalar_one_or_none()
            return connection
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error while fetching Connection: {e}")
            return None
