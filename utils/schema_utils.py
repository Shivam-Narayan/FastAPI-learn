from fastapi.exceptions import RequestValidationError
from logger import configure_logging
from db_pool import DatabasePoolManager

# Database modules
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
# async imports
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Default Libraries
from contextlib import contextmanager
from typing import Generator, AsyncGenerator, List, Optional, Union
from uuid import UUID
import os
import re
import subprocess

# Installed Libraries
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import decode
from dotenv import load_dotenv

load_dotenv()

db_pool = DatabasePoolManager()

logger = configure_logging(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authorize", auto_error=False)

RESERVED_SCHEMAS = { "information_schema", "pg_catalog", "pg_toast", "pg_temp_1", "pg_toast_temp_1" }

def run_alembic_migration(schema: str) -> None:
    try:
        command = ["alembic", "-x", f"tenant={schema}", "upgrade", "head"]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"Alembic migration failed for schema '{schema}': {result.stderr}")
            raise Exception(f"Alembic migration failed for schema '{schema}'")
        else:
            logger.info(f"Alembic migration succeeded for schema '{schema}': {result.stdout}")
    except Exception as e:
        logger.error(f"Error running Alembic migration for schema '{schema}': {e}")
        raise HTTPException(status_code=500, detail=f"Error running Alembic migration for schema '{schema}'")
    
def check_schema_exists(schema_name: str) -> bool:
    try:
        with db_pool.get_session("public") as db:
            result = db.execute(text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :name"), {"name": schema_name})
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking if schema '{schema_name}' exists: {e}")
        return False
    
def get_organization_schemas() -> Optional[list]:
    try:
        with db_pool.get_session("public") as db:
            result = db.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN :reserved")
            )
            schemas = [
                row[0]
                for row in result
                if row[0] not in RESERVED_SCHEMAS
            ]
            return schemas
    except Exception as e:
        logger.error(f"Error retrieving organization schemas: {e}")
        return None

def get_current_schema(db: Session) -> Optional[str]:
    try:
        current_schema = db.scalar(text("SELECT current_schema();"))
        return current_schema
    except Exception as e:
        logger.error(f"Error retrieving current schema: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving current schema")
    

def get_user_schemas(user_id: Union[UUID, str] = None) -> Optional[str]:
    try:
        with db_pool.get_session("public") as db:
            schemas = get_organization_schemas()
              
            if isinstance(user_id, UUID):
                where_clause = "id = :id"
            elif "@" in str(user_id):
                where_clause = "email = :id"
            else:
                where_clause = "user_id = :id"

            for schema in schemas:
                try:
                    quoted_schema = f'"{schema}"'
                    query = text(f"""
                        SELECT 1 
                        FROM {quoted_schema}.users 
                        WHERE {where_clause} 
                        LIMIT 1
                    """)
                    result = db.execute(query, {"id": str(user_id)})
                    if result.fetchone():
                        return schema
                except Exception as schema_error:
                    logger.error(f"Error checking user in schema '{schema}': {schema_error}")
                    continue

            return None
    except Exception as e:
        logger.error(f"Error retrieving user schemas: {e}")
        return None
    
@contextmanager
def set_schema(organization_schema: Optional[str] = None) -> Generator[Session, None, None]:

    try:
        schema_name = organization_schema if organization_schema is not None else "public"
        if not check_schema_exists(schema_name):
            logger.warning(f"Schema '{schema_name}' does not exist. Defaulting to 'public'.")
            raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found")
        
        with db_pool.get_session(schema_name) as db:
            yield Session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting schema to '{organization_schema}': {e}")
        raise HTTPException(status_code=500, detail=f"Error setting schema to '{organization_schema}'")


def get_schema_db(token: Optional[str] = Depends(oauth2_scheme),) -> Generator[Session, None, None]:
    """
    Dependency that returns a database session for a specific schema.
    Ensures the session is properly closed after each request.
    """
    try:
        schema_name = "public"

        if token:
            jwt_secret = os.getenv("JWT_SECRET")
            if not jwt_secret: 
                raise HTTPException(status_code=500, detail="JWT secret not configured")
            try:
                decoded_token = decode(token, jwt_secret, algorithms=["HS256"])
                schema_name = decoded_token.get("org_id", "public")
            except Exception as e:
                logger.error(f"Error decoding JWT token: {e}")
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            if not check_schema_exists(schema_name):
                logger.warning(f"Schema '{schema_name}' does not exist. Defaulting to 'public'.")
                raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found")
        
        with db_pool.get_session(schema_name) as Session:
            yield Session

    except HTTPException:
        raise
    except RequestValidationError:
        raise
    except Exception as e:
        logger.error(f"Error in get_schema_db dependency: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in database connection")


# --- ASYNC helpers --------------------------------------------------

# create an async session factory cache keyed by schema name
_async_session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}


def _get_async_session_factory(schema_name: str):
    """Return (and create if necessary) an async_sessionmaker bound to the given schema."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    if schema_name not in _async_session_factories:
        # convert sync DATABASE_URL to async+asyncpg driver
        url = os.getenv("DATABASE_URL")
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        engine = create_async_engine(url, future=True)

        # ensure the schema search path is set at session start
        def on_connect(dbapi_connection, connection_record):
            # sync event handler invoked on each new connection
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute(f"SET search_path TO '{schema_name}'")
            finally:
                cursor.close()

        # SQLAlchemy async engines expose sync engine for events
        from sqlalchemy import event
        event.listen(engine.sync_engine, "connect", on_connect)

        _async_session_factories[schema_name] = async_sessionmaker(bind=engine, expire_on_commit=False)
    return _async_session_factories[schema_name]


async def get_async_schema_db(token: Optional[str] = Depends(oauth2_scheme)) -> AsyncGenerator[AsyncSession, None]:
    """Async dependency to provide an AsyncSession scoped to a tenant schema."""
    from sqlalchemy.ext.asyncio import AsyncSession

    try:
        schema_name = "public"

        if token:
            jwt_secret = os.getenv("JWT_SECRET")
            if not jwt_secret:
                raise HTTPException(status_code=500, detail="JWT secret not configured")
            try:
                decoded_token = decode(token, jwt_secret, algorithms=["HS256"])
                schema_name = decoded_token.get("org_id", "public")
            except Exception as e:
                logger.error(f"Error decoding JWT token: {e}")
                raise HTTPException(status_code=401, detail="Invalid authentication token")

            if not check_schema_exists(schema_name):
                logger.warning(f"Schema '{schema_name}' does not exist. Defaulting to 'public'.")
                raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found")

        session_factory = _get_async_session_factory(schema_name)
        async with session_factory() as session:
            # ensure search path is set (redundant with connect hook but safe)
            await session.execute(text(f"SET search_path TO '{schema_name}'"))
            yield session

    except HTTPException:
        raise
    except RequestValidationError:
        raise
    except Exception as e:
        logger.error(f"Error in get_async_schema_db dependency: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in database connection")
    
@contextmanager
def get_session_for_role(
    user_role: str,
    injected_db: Session,
    root_schema: str = "public"
) -> Generator[Session, None, None]:
    """
    Context manager to get a database session with the appropriate role for the current user.
    """
    if user_role == "ROOT":
        with set_schema(root_schema) as root_db:
            yield root_db
    else:
        yield injected_db