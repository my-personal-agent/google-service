import logging

from config.logging_config import setup_logging
from config.settings_config import get_settings
from google_mcp.server import mcp

setup_logging()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import google_mcp.custom_routes  # noqa: F401
    import google_mcp.tools  # noqa: F401

    mcp.run(transport=get_settings().mcp_transport.value)
    logger.info(f"Started {get_settings().project_info}")
