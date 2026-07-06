import os
import smtplib
from email.mime.text import MIMEText
import requests

def send_discord(message: str):
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    # Discord caps a single message at 2000 characters — trim just in case a report runs long.
    resp = requests.post(webhook_url, json={"content": message[:2000]})
    resp.raise_for_status()
    return resp.status_code

def send_email(subject: str, body: str):
    """Sends an email via Gmail's SMTP server using an App Password
    (never your real Gmail password — see Section 8 for setup)."""
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    # Defaults to emailing yourself if GMAIL_RECIPIENT isn't set separately.
    recipient = os.environ.get("GMAIL_RECIPIENT", sender)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, [recipient], msg.as_string())
