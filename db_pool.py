# Standard library imports
import os
import threading
import asyncio
from contextlib import contextmanager, asynccontextmanager
from typing import Dict, Generator, AsyncGenerator, Any

# Third-party imports
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from logger import configure_logging

logger = configure_logging(__name__)

# Base class for declarative models (shared across all schemas)
Base = declarative_base()


class DatabasePoolManager:
    _instance = None
    _engines: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePoolManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        # Set reasonable pool size limits
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "2"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "50"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        self._session_factories = {}

    def get_engine(self, schema_name: str):
        """Get or create an engine for a specific schema"""
        if schema_name not in self._engines:
            engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,  # Wait timeout for connection
                pool_pre_ping=True,  # Ensures connections are valid
                pool_recycle=self.pool_recycle,  # Recycle connections periodically
            )

            # Set schema for all connections from this engine
            @event.listens_for(engine, "connect")
            def set_search_path(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                try:
                    cursor.execute(f"SET search_path TO '{schema_name}'")
                finally:
                    cursor.close()

            # Set schema for every session checkout to ensure correct schema context
            @event.listens_for(engine, "checkout")
            def set_search_path_on_checkout(
                dbapi_connection, connection_record, connection_proxy
            ):
                cursor = dbapi_connection.cursor()
                try:
                    cursor.execute(f"SET search_path TO '{schema_name}'")
                finally:
                    cursor.close()

            self._engines[schema_name] = engine

        return self._engines[schema_name]

    def get_session_factory(self, schema_name: str) -> sessionmaker:
        """Get or create a session factory for a specific schema"""
        if schema_name not in self._session_factories:
            engine = self.get_engine(schema_name)
            self._session_factories[schema_name] = sessionmaker(
                bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
            )
        return self._session_factories[schema_name]

    def create_session(self, schema: str) -> Session:
        """
        Get a raw session object for a specific schema.
        This should be used only for short-lived operations and local testing.
        """
        session_factory = self.get_session_factory(schema)
        return session_factory()

    @contextmanager
    def get_session(
        self, schema_name: str = "public"
    ) -> Generator[Session, None, None]:
        """Get a database session for a specific schema"""
        session_factory = self.get_session_factory(schema_name)
        session = session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose_all(self):
        """Clean up all synchronous database connections"""
        for engine in self._engines.values():
            engine.dispose()


# --- Async Pool Manager ---
class AsyncDatabasePoolManager:
    _instance = None
    _pools: Dict[str, AsyncConnectionPool] = {}
    _pool_creation_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncDatabasePoolManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.database_url = os.getenv("DATABASE_URL")

        # Reuse sync pool settings for consistency (DB_POOL_SIZE + DB_MAX_OVERFLOW)
        base_pool_size = int(os.getenv("DB_POOL_SIZE", "2"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "3"))
        self.min_pool_size = base_pool_size
        self.max_pool_size = base_pool_size + max_overflow
        # Note: AsyncDatabasePoolManager is currently unused - LangGraph manages async pools
        self._initialized = True

    async def _configure_connection(self, conn, schema_name: str):
        """Sets the search_path for a new connection."""
        async with conn.cursor() as cur:
            # Use parameterized query for safety
            await cur.execute("SET search_path TO %s", (schema_name,))

    def get_pool(self, schema_name: str) -> AsyncConnectionPool:
        """Get or create an async connection pool for a specific schema."""
        if schema_name not in self._pools:
            with self._pool_creation_lock:
                if schema_name not in self._pools:
                    conninfo = make_conninfo(self.database_url)
                    pool = AsyncConnectionPool(
                        conninfo=conninfo,
                        min_size=self.min_pool_size,
                        max_size=self.max_pool_size,
                        # The configure hook is suitable for setting search_path
                        configure=lambda conn: self._configure_connection(
                            conn, schema_name
                        ),
                        check=AsyncConnectionPool.check_connection,
                        # Pass connection kwargs here
                        kwargs={
                            "row_factory": dict_row,
                            "autocommit": True,
                            "prepare_threshold": None,
                        },
                        name=f"pool_{schema_name}",
                    )
                    self._pools[schema_name] = pool

        return self._pools[schema_name]

    @asynccontextmanager
    async def get_connection(
        self, schema_name: str = "public"
    ) -> AsyncGenerator[psycopg.AsyncConnection, None]:
        """Provides an async database connection from the pool for the specified schema."""
        pool = self.get_pool(schema_name)
        conn = None
        try:
            async with pool.connection() as conn:
                yield conn
        except Exception as e:
            # Consider adding logging here for production
            raise

    async def close_all(self):
        """Closes all managed async connection pools."""
        # logger.info("Closing all async connection pools...")
        closing_tasks = [pool.close() for pool in self._pools.values()]
        await asyncio.gather(*closing_tasks)
        self._pools.clear()
        # logger.info("All async connection pools closed.")

# Initialize default engine for the application
db_manager = DatabasePoolManager()
engine = db_manager.get_engine("public")