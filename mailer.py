import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

# These must be set in your .env file (see setup notes).
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # SSL


def send_reset_email(to_email, reset_link):
    """Sends a password reset email with the given link. Raises an exception
    if sending fails, so callers should wrap this in a try/except."""
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        raise RuntimeError(
            "EMAIL_ADDRESS / EMAIL_APP_PASSWORD are not set in your .env file."
        )

    subject = "Reset your Taro password"
    body = (
        "Hello,\n\n"
        "We received a request to reset the password for your Taro account.\n\n"
        f"Click the link below to choose a new password:\n{reset_link}\n\n"
        "This link will expire in 1 hour. If you did not request this, "
        "you can safely ignore this email — your password will not change.\n\n"
        "— Taro"
    )

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = EMAIL_ADDRESS
    message["To"] = to_email

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())