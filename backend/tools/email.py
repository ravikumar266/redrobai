import logging
import asyncio
import base64
from email.mime.text import MIMEText
from typing import Any, Dict
from pathlib import Path
from backend.tools.base import BaseTool
from backend.config import settings

logger = logging.getLogger(__name__)


def _build_google_services():
    """
    Builds and returns authenticated Gmail, Docs, and Drive API service objects.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    # API scopes: Gmail send, Docs write, Drive write (for permissions)
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.file"
    ]

    # Resolve file paths relative to the project root
    from backend.config import BASE_DIR
    credentials_path = BASE_DIR / settings.GMAIL_CREDENTIALS_FILE
    token_path = BASE_DIR / settings.GMAIL_TOKEN_FILE

    creds = None

    # Step 1: Load existing token if available
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # Step 2: Refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token expired but refresh token exists → auto-refresh
            logger.info("Google token expired. Refreshing...")
            creds.refresh(Request())
        else:
            # No token at all → run interactive OAuth2 flow (first-time setup)
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"Google credentials file not found at '{credentials_path}'. "
                )
            logger.info("No valid Google token found (or scopes changed). Starting OAuth2 authorization flow...")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Step 3: Save the token for future runs
        token_path.write_text(creds.to_json())
        logger.info(f"Google token saved to {token_path}")

    # Step 4: Build and return the API services
    return {
        "gmail": build("gmail", "v1", credentials=creds),
        "docs": build("docs", "v1", credentials=creds),
        "drive": build("drive", "v3", credentials=creds)
    }


class EmailTool(BaseTool):
    """
    Tool to send evaluation report emails using the Gmail API.

    How it works:
    1. Builds a MIME email message (plain text).
    2. Base64url-encodes the message (required by Gmail API).
    3. Calls gmail.users().messages().send() to deliver the email.

    Setup required (one-time):
    1. Enable Gmail API in Google Cloud Console.
    2. Create OAuth2 credentials (Desktop App type).
    3. Download credentials.json to the project root.
    4. On first run, a browser window opens for login → generates token.json.
    """
    name: str = "EmailTool"
    description: str = "Sends evaluation report emails to recruiters using the Gmail API."

    async def run(self, to_email: str, subject: str, body: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Send an email via Gmail API.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            body: Plain text email body.

        Returns:
            Dict with delivery status and Gmail message ID.
        """
        logger.info(f"EmailTool sending message to: {to_email}")
        from_email = settings.GMAIL_SENDER_EMAIL

        # Check if credentials file exists before attempting
        from backend.config import BASE_DIR
        credentials_path = BASE_DIR / settings.GMAIL_CREDENTIALS_FILE
        if not credentials_path.exists():
            logger.warning(
                f"Gmail credentials.json not found. MOCK EMAIL LOGGED BELOW:\n"
                f"--------------------------------------------------\n"
                f"TO: {to_email}\n"
                f"FROM: {from_email}\n"
                f"SUBJECT: {subject}\n"
                f"BODY:\n{body}\n"
                f"--------------------------------------------------"
            )
            return {
                "to": to_email,
                "subject": subject,
                "sent_status": "mocked_logged",
                "message": "Email logged because credentials.json is not configured."
            }

        try:
            # Build the MIME message
            mime_message = MIMEText(body)
            mime_message["to"] = to_email
            mime_message["from"] = from_email
            mime_message["subject"] = subject

            # Encode to base64url format (Gmail API requirement)
            raw_message = base64.urlsafe_b64encode(
                mime_message.as_bytes()
            ).decode("utf-8")

            # Send via Gmail API (run in thread to keep async)
            def _send():
                services = _build_google_services()
                gmail_service = services["gmail"]
                result = gmail_service.users().messages().send(
                    userId="me",
                    body={"raw": raw_message}
                ).execute()
                return result

            result = await asyncio.to_thread(_send)

            logger.info(f"Email sent successfully via Gmail API. Message ID: {result.get('id')}")
            return {
                "to": to_email,
                "subject": subject,
                "sent_status": "delivered",
                "gmail_message_id": result.get("id"),
                "message": "Email sent successfully via Gmail API."
            }

        except FileNotFoundError as e:
            logger.error(f"EmailTool: {e}")
            return {
                "to": to_email,
                "subject": subject,
                "sent_status": "failed",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"EmailTool Gmail API call failed: {e}")
            return {
                "to": to_email,
                "subject": subject,
                "sent_status": "failed",
                "error": str(e)
            }
