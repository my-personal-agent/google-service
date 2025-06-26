import logging
import os

import psutil
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from core.monitoring import cpu_usage, memory_usage
from google_mcp.server import mcp

logger = logging.getLogger(__name__)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> JSONResponse:
    """
    Health check endpoint to verify if the service is alive.
    This endpoint does not perform any external API calls and simply returns a 200 OK response.
    """
    logger.debug("Health check endpoint called")
    return JSONResponse(status_code=200, content={"status": "alive"})


@mcp.custom_route("/readyz", methods=["GET"])
async def readyz(request: Request) -> JSONResponse:
    """
    Readiness check endpoint to verify if the service is ready to handle requests.
    This endpoint checks the OpenWeather API to ensure it is reachable.
    If the API is reachable, it returns a 200 OK response.
    If the API is not reachable, it returns a 503 Service Unavailable response.
    """
    logger.debug("Readiness check endpoint called")
    return JSONResponse(status_code=200, content={"status": "ready"})


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(request: Request) -> PlainTextResponse:
    """
    Metrics endpoint to expose application and system metrics in Prometheus format.
    This endpoint collects metrics such as tool calls, execution time, active connections,
    memory usage, and CPU usage.
    """
    logger.debug("Metrics endpoint called")
    process = psutil.Process(os.getpid())
    memory_usage.set(process.memory_info().rss)
    cpu_usage.set(process.cpu_percent())

    return PlainTextResponse(
        generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST}
    )
