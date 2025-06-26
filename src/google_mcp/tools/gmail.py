import logging
from typing import Annotated, Any

from mcp.server.fastmcp import Context
from pydantic import BeforeValidator, EmailStr, Field

from google_mcp.server import mcp
from services.gmail_service import send_gmail_mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def send_gmail(
    ctx: Context,
    user_id: Annotated[
        str,
        BeforeValidator(str.strip),
        Field(
            min_length=1,
            description="Unique identifier for the user sending the email. Used for authentication and rate limiting.",
        ),
    ],
    to: Annotated[
        EmailStr,
        Field(
            description="Recipient email address. Must be a valid email format (e.g., user@example.com)."
        ),
    ],
    subject: Annotated[
        str,
        BeforeValidator(str.strip),
        Field(
            min_length=1,
            max_length=998,  # RFC 5322 limit
            description="Email subject line. Cannot be empty and should be descriptive of the email content.",
        ),
    ],
    body: Annotated[
        str,
        BeforeValidator(str.strip),
        Field(
            min_length=1,
            description="Email body content. Supports plain text and HTML formatting. Cannot be empty.",
        ),
    ],
) -> dict[str, Any]:
    """
    Send an email via Gmail API through Model Context Protocol.

    This tool enables sending emails through Gmail's API with proper authentication
    and error handling. The tool validates input parameters, handles rate limiting,
    and provides detailed response information.

    Args:
        user_id (str): Unique identifier for the authenticated user. Used for:
            - Authentication verification
            Must be a non-empty string after stripping whitespace.

        to (EmailStr): Recipient's email address. Must be a valid email format
            as validated by Pydantic's EmailStr type. Examples:
            - "user@example.com"
            - "firstname.lastname@company.org"

        subject (str): Email subject line. Must be:
            - Non-empty after stripping whitespace
            - Maximum 998 characters (RFC 5322 limit)
            - Descriptive of email content

        body (str): Email message body. Must be:
            - Non-empty after stripping whitespace
            - Can contain plain text or HTML
            - Supports Unicode characters

    Returns:
        Dict[str, Any]: Response dictionary containing:
            - success (bool): Whether the email was sent successfully
            - message_id (str): Gmail message ID if successful
            - timestamp (str): ISO timestamp of when email was sent

    Raises:
        ValueError: If any input parameter is invalid after validation
        AuthenticationError: If user_id is not authenticated or token is invalid
        RateLimitError: If user has exceeded their rate limit
        APIError: If Gmail API returns an error
        NetworkError: If there's a network connectivity issue

    Examples:
        >>> # Send a simple text email
        >>> result = await send_gmail(
        ...     user_id="user123",
        ...     to="recipient@example.com",
        ...     subject="Hello from MCP",
        ...     body="This is a test email sent via MCP tool."
        ... )
        >>> print(result['success'])  # True

        >>> # Send an HTML email
        >>> html_body = '''
        ... <html>
        ...   <body>
        ...     <h1>Welcome!</h1>
        ...     <p>This is an <strong>HTML</strong> email.</p>
        ...   </body>
        ... </html>
        ... '''
        >>> result = await send_gmail(
        ...     user_id="user123",
        ...     to="recipient@example.com",
        ...     subject="HTML Email Test",
        ...     body=html_body
        ... )

    Notes:
        - HTML content in body will be automatically detected and processed
        - All emails are sent from the authenticated user's Gmail account
    """
    return await send_gmail_mcp(user_id, to, subject, body, mcp_ctx=ctx)
