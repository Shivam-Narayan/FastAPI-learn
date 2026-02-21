# Custom libraries
from logger import configure_logging
from models.connection import Connection

# Default libraries
from typing import Optional, List
from uuid import UUID

# Installed libraries
from fastapi import HTTPException
from sqlalchemy import select, func
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
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error while fetching Connection: {e}")
            return None

    async def list_connections(self) -> List[Connection]:
        try:
            result = await self.db.execute(
                select(Connection).filter(Connection.deleted_at.is_(None))
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error while listing connections: {e}")
            return []

    async def update_connection(self, connection_id: UUID, updates: dict) -> Optional[Connection]:
        conn = await self.get_connection_by_id(connection_id)
        if not conn:
            return None
        try:
            for k, v in updates.items():
                if hasattr(conn, k) and k != 'id':
                    setattr(conn, k, v)
            await self.db.commit()
            await self.db.refresh(conn)
            return conn
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"SQLAlchemy Error while updating Connection: {e}")
            return None

    async def soft_delete_connection(self, connection_id: UUID) -> bool:
        conn = await self.get_connection_by_id(connection_id)
        if not conn:
            return False
        try:
            conn.deleted_at = func.now()
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"SQLAlchemy Error while deleting Connection: {e}")
            return False
