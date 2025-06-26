import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from config.settings_config import get_settings
from db.prisma.utils import get_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting up {get_settings().project_info}...")

    # load db
    db = await get_db()

    # set data
    app.state.ready = True

    # log
    logger.info(f"{get_settings().project_info} completely loaded")

    yield

    # Shutdown
    logger.info(f"Shutting down {get_settings().project_info}...")

    # Add cleanup tasks
    await db.disconnect()

    logger.info(f"{get_settings().project_info} completely shutdown")
