# Custom libraries
from logger import configure_logging
from utils.schema_utils import get_current_schema

# Default libraries
from typing import List, Optional
from uuid import UUID

# Installed libraries
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = configure_logging(__name__)

def parse_identifier(identifier):
    # If already a UUID object, return as-is
    if isinstance(identifier, UUID):
        return identifier

    try:
        # Check if the string representation matches the original
        return UUID(identifier)
    except (ValueError, AttributeError):
        # If an error is raised, it is not a valid UUID
        return identifier
