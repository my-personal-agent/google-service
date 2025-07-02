import logging
from typing import Annotated, Any, List, Optional, Union

from mcp.server.fastmcp import Context
from pydantic import BeforeValidator, EmailStr, Field

from google_mcp.server import mcp
from services.gmail_service import send_gmail_mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def send_gmail(
    ctx: Context,
    gmail_user_id: Annotated[
        str,
        BeforeValidator(str.strip),
        Field(
            min_length=1,
            description="Unique identifier for the user sending the email.",
        ),
    ],
    to: Annotated[
        Union[EmailStr, List[EmailStr]],
        Field(
            description="Recipient email address(es). Can be a single email string or a list of email addresses. All must be valid email formats (e.g., 'user@example.com' or ['user1@example.com', 'user2@example.com'])."
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
    cc: Annotated[
        Optional[Union[EmailStr, List[EmailStr]]],
        Field(
            default=None,
            description="CC (Carbon Copy) email address(es). Optional. Can be a single email string or a list of email addresses. All must be valid email formats.",
        ),
    ] = None,
    bcc: Annotated[
        Optional[Union[EmailStr, List[EmailStr]]],
        Field(
            default=None,
            description="BCC (Blind Carbon Copy) email address(es). Optional. Can be a single email string or a list of email addresses. All must be valid email formats.",
        ),
    ] = None,
) -> dict[str, Any]:
    """
    Send an email via Gmail API through Model Context Protocol.

    This tool enables sending emails through Gmail's API with proper authentication
    and error handling. The tool validates input parameters, handles rate limiting,
    and provides detailed response information. Supports multiple recipients and CC/BCC.

    Args:
        gmail_user_id (str): Unique identifier for the authenticated user. Used for:
            - Sending gmail
            Must be a non-empty string after stripping whitespace.

        to (Union[EmailStr, List[EmailStr]]): Primary recipient email address(es).
            Can be:
            - Single email: "user@example.com"
            - Multiple emails: ["user1@example.com", "user2@example.com"]
            All addresses must be valid email formats.

        subject (str): Email subject line. Must be:
            - Non-empty after stripping whitespace
            - Maximum 998 characters (RFC 5322 limit)
            - Descriptive of email content

        body (str): Email message body. Must be:
            - Non-empty after stripping whitespace
            - Can contain plain text or HTML
            - Supports Unicode characters

        cc (Optional[Union[EmailStr, List[EmailStr]]]): CC recipients. Optional.
            Can be:
            - Single email: "cc@example.com"
            - Multiple emails: ["cc1@example.com", "cc2@example.com"]
            - None (default): No CC recipients

        bcc (Optional[Union[EmailStr, List[EmailStr]]]): BCC recipients. Optional.
            Can be:
            - Single email: "bcc@example.com"
            - Multiple emails: ["bcc1@example.com", "bcc2@example.com"]
            - None (default): No BCC recipients

    Returns:
        Dict[str, Any]: Response dictionary containing:
            - success (bool): Whether the email was sent successfully
            - message_id (str): Gmail message ID if successful
            - timestamp (str): ISO timestamp of when email was sent
            - recipients (dict): Summary of recipients:
                - to (List[str]): List of primary recipients
                - cc (List[str]): List of CC recipients (if any)
                - bcc (List[str]): List of BCC recipients (if any)

    Raises:
        ValueError: If any input parameter is invalid after validation
        AuthenticationError: If gmail_user_id is not authenticated or token is invalid
        RateLimitError: If user has exceeded their rate limit
        APIError: If Gmail API returns an error
        NetworkError: If there's a network connectivity issue

    Examples:
        >>> # Send to single recipient
        >>> result = await send_gmail(
        ...     gmail_user_id="user123",
        ...     to="recipient@example.com",
        ...     subject="Hello from MCP",
        ...     body="This is a test email sent via MCP tool."
        ... )

        >>> # Send to multiple recipients
        >>> result = await send_gmail(
        ...     gmail_user_id="user123",
        ...     to=["recipient1@example.com", "recipient2@example.com"],
        ...     subject="Team Update",
        ...     body="This email goes to multiple recipients."
        ... )

        >>> # Send with CC and BCC
        >>> result = await send_gmail(
        ...     gmail_user_id="user123",
        ...     to="primary@example.com",
        ...     cc=["manager@example.com", "team@example.com"],
        ...     bcc="archive@example.com",
        ...     subject="Project Status",
        ...     body="Status update with CC to management and team."
        ... )

        >>> # Send HTML email with multiple recipients
        >>> html_body = '''
        ... <html>
        ...   <body>
        ...     <h1>Welcome Team!</h1>
        ...     <p>This is an <strong>HTML</strong> email for everyone.</p>
        ...   </body>
        ... </html>
        ... '''
        >>> result = await send_gmail(
        ...     gmail_user_id="user123",
        ...     to=["team1@example.com", "team2@example.com"],
        ...     cc="supervisor@example.com",
        ...     subject="HTML Team Email",
        ...     body=html_body
        ... )

    Notes:
        - HTML content in body will be automatically detected and processed
        - All emails are sent from the authenticated user's Gmail account
        - When using multiple recipients, each address is validated individually
        - CC recipients can see all other recipients (TO and CC)
        - BCC recipients are hidden from all other recipients
        - Maximum recommended recipients per email: 100 (Gmail limit)
    """

    # Normalize recipients to lists for consistent processing
    def normalize_recipients(recipients) -> List[str]:
        if recipients is None:
            return []
        elif isinstance(recipients, str):
            return [recipients]
        elif isinstance(recipients, list):
            return recipients
        else:
            return [recipients]  # Handle EmailStr objects

    to_list = normalize_recipients(to)
    cc_list = normalize_recipients(cc)
    bcc_list = normalize_recipients(bcc)

    return await send_gmail_mcp(
        gmail_user_id,
        to_list,
        subject,
        body,
        mcp_ctx=ctx,
        cc=cc_list if cc_list else None,
        bcc=bcc_list if bcc_list else None,
    )
