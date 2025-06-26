from mcp.server.fastmcp import FastMCP

from config.settings_config import get_settings

mcp = FastMCP(
    get_settings().project_name,
    host=get_settings().mcp_host,
    port=get_settings().mcp_port,
)
