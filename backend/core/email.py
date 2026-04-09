"""
Simple SMTP email sender.

Requires env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, APP_BASE_URL.
If SMTP_HOST is not set, emails are printed to stdout (dev mode).
"""

import logging
import smtplib
from email.mime.text import MIMEText

from core.config import APP_BASE_URL, SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER

logger = logging.getLogger(__name__)


def send_login_link(to_email: str, token: str):
    link = f"{APP_BASE_URL}/verify-login?token={token}"
    subject = "Your login link"
    body = f"Click the link below to complete your login. It expires in 15 minutes.\n\n{link}\n\nIf you did not request this, ignore this email."

    if not SMTP_HOST:
        logger.warning(f"[DEV] Login link for {to_email}: {link}")
        print(f"\n[DEV] Login link for {to_email}:\n  {link}\n")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())
        logger.info(f"Login link sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send login link to {to_email}: {e}")
        raise
