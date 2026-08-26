import os
import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")  # must match the verified sender in Brevo

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_reset_email(to_email, reset_link):
    """Sends a password reset email with the given link, via Brevo's HTTP API
    (not SMTP). Raises an exception if sending fails, so callers should wrap
    this in a try/except.

    Uses HTTPS instead of SMTP because Render's free tier blocks outbound
    traffic on SMTP ports (25, 465, 587), but does not block HTTPS.
    """
    if not BREVO_API_KEY or not SENDER_EMAIL:
        raise RuntimeError(
            "BREVO_API_KEY / SENDER_EMAIL are not set in your .env file."
        )

    body_text = (
        "Hello,\n\n"
        "We received a request to reset the password for your Taro account.\n\n"
        f"Click the link below to choose a new password:\n{reset_link}\n\n"
        "This link will expire in 1 hour. If you did not request this, "
        "you can safely ignore this email — your password will not change.\n\n"
        "— Taro"
    )

    payload = {
        "sender": {"email": SENDER_EMAIL, "name": "Taro"},
        "to": [{"email": to_email}],
        "subject": "Reset your Taro password",
        "textContent": body_text,
    }
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
    if response.status_code >= 300:
        raise RuntimeError(
            f"Brevo email send failed ({response.status_code}): {response.text}"
        )