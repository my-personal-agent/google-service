import base64
import logging
from datetime import datetime, timezone

from googleapiclient.discovery import build
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from services.auth_service import get_creds

logger = logging.getLogger(__name__)


async def send_gmail_mcp(
    gmail_user_id: str,
    to: str,
    subject: str,
    body: str,
    mcp_ctx: Context,
) -> dict[str, str]:
    """
    Send an email via Gmail API using stored OAuth credentials.
    """
    await mcp_ctx.info(
        f"Starting email send (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
    )
    logger.info(
        "Starting email send",
        extra={
            "request_id": mcp_ctx.request_id,
            "client_id": mcp_ctx.client_id,
        },
    )

    try:
        creds = await get_creds(gmail_user_id)
        await mcp_ctx.info(
            f"Retrieved user credentials (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
        )
        logger.info(
            "Retrieved user credentials",
            extra={
                "request_id": mcp_ctx.request_id,
                "client_id": mcp_ctx.client_id,
            },
        )

        service = build("gmail", "v1", credentials=creds)
        await mcp_ctx.info("Built Gmail service client")

        # Build email content and encode
        message = f"To: {to}\nSubject: {subject}\n\n{body}"
        raw = base64.urlsafe_b64encode(message.encode()).decode()

        # Optionally report progress at 50%
        await mcp_ctx.report_progress(
            progress=50, total=100, message="Calling Google API"
        )

        # Send the message
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        await mcp_ctx.info(
            f"Email sent, messageId={sent.get('id')} (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
        )
        logger.info(
            f"Email sent, messageId={sent.get('id')}",
            extra={
                "request_id": mcp_ctx.request_id,
                "client_id": mcp_ctx.client_id,
            },
        )

        # Completion at 100%
        await mcp_ctx.report_progress(
            progress=100, total=100, message="Email sent successfully"
        )

        return {
            "success": "true",
            "message_id": sent.get("id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        await mcp_ctx.error(
            f"Failed to send Gmail: {e} (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
        )
        logger.error(
            f"Failed to send Gmail: {e}",
            extra={
                "request_id": mcp_ctx.request_id,
                "client_id": mcp_ctx.client_id,
            },
        )
        raise ToolError(f"Gmail send failed: {e}")
