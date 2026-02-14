# Custom libraries
from logger import configure_logging
from schemas.connection_schema import ConnectionCreate, ConnectionDetail
from repository.connection_repository import ConnectionRepository
from utils.schema_utils import get_async_schema_db

# Database modules
from sqlalchemy.ext.asyncio import AsyncSession

# Default libraries
from uuid import UUID

# Installed libraries
from fastapi import APIRouter, Body, Depends, HTTPException, Path


logger = configure_logging(__name__)

connection_router = APIRouter(tags=["Connections"])



@connection_router.get("/connections/{connection_id}", response_model=ConnectionDetail)
async def get_connection(
    connection_id: UUID = Path(..., description="Connection UUID"),
    db: AsyncSession = Depends(get_async_schema_db),
):
    """
    Retrieves a connection by its UUID.

    Returns 404 if connection not found or soft-deleted.
    """
    try:
        connection_repository = ConnectionRepository(db)

        connection = await connection_repository.get_connection_by_id(connection_id)

        if connection:
            return ConnectionDetail.model_validate(connection)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Connection with id {connection_id} not found.",
            )

    except HTTPException as http_error:
        logger.error(f"HTTPException occurred: {http_error.detail}")
        raise http_error
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@connection_router.post("/connections", response_model=ConnectionDetail)
async def create_connection(
    connection_data: ConnectionCreate = Body(...),
    db: AsyncSession = Depends(get_async_schema_db),
):
    """
    Creates a new connection.

    Validates provider_key against INTEGRATIONS config and auth_schema_key against AUTH_SCHEMAS config.
    """
    try:
        connection_repository = ConnectionRepository(db)

        connection = await connection_repository.create_connection(connection_data)

        if connection:
            logger.info(f"Connection '{connection.name}' created successfully: {connection.id}")
            return ConnectionDetail.model_validate(connection)
        else:
            raise HTTPException(status_code=400, detail="Failed to create Connection.")

    except HTTPException as http_error:
        logger.error(f"HTTPException occurred: {http_error.detail}")
        raise http_error
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


