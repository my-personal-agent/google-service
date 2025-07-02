import base64
import logging
import re
from datetime import datetime, timezone
from typing import Any, List, Optional

from googleapiclient.discovery import build
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from services.auth_service import get_creds

logger = logging.getLogger(__name__)


async def send_gmail_mcp(
    gmail_user_id: str,
    to: List[str],
    subject: str,
    body: str,
    mcp_ctx: Context,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
) -> dict[str, Any]:
    """
    Send an email via Gmail API using stored OAuth credentials.

    Args:
        gmail_user_id: User identifier for OAuth credentials
        to: List of primary recipient email addresses
        subject: Email subject line
        body: Email body content (plain text or HTML)
        mcp_ctx: MCP context for logging and progress reporting
        cc: Optional list of CC recipient email addresses
        bcc: Optional list of BCC recipient email addresses

    Returns:
        Dict containing success status, message ID, timestamp, and recipient summary
    """
    await mcp_ctx.info(
        f"Starting email send (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
    )
    logger.info(
        "Starting email send",
        extra={
            "request_id": mcp_ctx.request_id,
            "client_id": mcp_ctx.client_id,
            "to_count": len(to),
            "cc_count": len(cc) if cc else 0,
            "bcc_count": len(bcc) if bcc else 0,
        },
    )

    try:
        # Validate inputs
        if not to:
            raise ValueError("At least one recipient in 'to' field is required")

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

        # Build email message with proper RFC 5322 formatting
        message_parts = []

        # Add To header
        message_parts.append(f"To: {', '.join(to)}")

        # Add CC header if provided
        if cc:
            message_parts.append(f"Cc: {', '.join(cc)}")

        # Add BCC header if provided (note: BCC won't be visible in sent email)
        if bcc:
            message_parts.append(f"Bcc: {', '.join(bcc)}")

        # Add subject
        message_parts.append(f"Subject: {subject}")

        # Detect if body contains HTML
        is_html = bool(re.search(r"<[^>]+>", body))
        if is_html:
            message_parts.append("Content-Type: text/html; charset=utf-8")
        else:
            message_parts.append("Content-Type: text/plain; charset=utf-8")

        # Add empty line before body (RFC 5322 requirement)
        message_parts.append("")
        message_parts.append(body)

        # Join all parts with CRLF line endings
        message = "\r\n".join(message_parts)

        # Encode message for Gmail API
        raw = base64.urlsafe_b64encode(message.encode("utf-8")).decode("ascii")

        # Report progress at 50%
        await mcp_ctx.report_progress(
            progress=50, total=100, message="Calling Gmail API"
        )

        # Send the message
        request_body = {"raw": raw}
        sent = service.users().messages().send(userId="me", body=request_body).execute()

        message_id = sent.get("id")
        timestamp = datetime.now(timezone.utc).isoformat()

        await mcp_ctx.info(
            f"Email sent successfully, messageId={message_id} (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
        )
        logger.info(
            f"Email sent successfully, messageId={message_id}",
            extra={
                "request_id": mcp_ctx.request_id,
                "client_id": mcp_ctx.client_id,
                "message_id": message_id,
            },
        )

        # Report completion at 100%
        await mcp_ctx.report_progress(
            progress=100, total=100, message="Email sent successfully"
        )

        # Build recipient summary for response
        recipients_summary = {
            "to": to,
            "cc": cc if cc else [],
            "bcc": bcc if bcc else [],
        }

        return {
            "success": True,  # Return boolean instead of string
            "message_id": message_id,
            "timestamp": timestamp,
            "recipients": recipients_summary,
            "total_recipients": len(to)
            + (len(cc) if cc else 0)
            + (len(bcc) if bcc else 0),
        }

    except ValueError as ve:
        error_msg = f"Invalid input: {ve}"
        await mcp_ctx.error(
            f"{error_msg} (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
        )
        logger.error(
            error_msg,
            extra={
                "request_id": mcp_ctx.request_id,
                "client_id": mcp_ctx.client_id,
            },
        )
        raise ToolError(error_msg)

    except Exception as e:
        error_msg = f"Gmail send failed: {str(e)}"
        await mcp_ctx.error(
            f"{error_msg} (request_id={mcp_ctx.request_id}, client_id={mcp_ctx.client_id})"
        )
        logger.error(
            error_msg,
            extra={
                "request_id": mcp_ctx.request_id,
                "client_id": mcp_ctx.client_id,
                "error_type": type(e).__name__,
            },
        )
        raise ToolError(error_msg)
