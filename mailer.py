import os
import socket
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

# These must be set in your .env file (see setup notes).
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # SSL

# --------------------------------------------------------------------------
# Some hosts (Render's free/starter containers, in particular) have no
# outbound IPv6 route. smtp.gmail.com publishes both an IPv4 and an IPv6
# address, and Python's default resolver sometimes picks the IPv6 one first
# — which then fails immediately with "[Errno 101] Network is unreachable".
# Forcing getaddrinfo to only return IPv4 results fixes it, and it's safe:
# the connection is still made to "smtp.gmail.com" by hostname, so TLS
# certificate verification is unaffected.
# --------------------------------------------------------------------------
_original_getaddrinfo = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    results = _original_getaddrinfo(host, port, family, type, proto, flags)
    ipv4_results = [r for r in results if r[0] == socket.AF_INET]
    return ipv4_results or results  # fall back to whatever we got if no IPv4 found


socket.getaddrinfo = _ipv4_only_getaddrinfo


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