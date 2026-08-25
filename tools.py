"""
tools.py
Real-world actions the agent can take:
  - send_email()            -> sends an actual email via Gmail
  - create_calendar_event() -> creates an actual event on Google Calendar

Both use OAuth2 against your own Google account (not a service account),
so the first run will open a browser window asking you to log in and approve.
"""

import os
import pickle
import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes define exactly what this app is allowed to do with your account.
# gmail.send  -> can send email, cannot read your inbox
# calendar    -> can create/read/update events on your calendars
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

CREDENTIALS_FILE = "credentials.json"   # downloaded from Google Cloud Console
TOKEN_FILE = "token.pickle"             # auto-created after first login


def get_credentials():
    """
    Returns valid OAuth2 credentials, running the browser login flow
    only if no valid token is cached yet.
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    "credentials.json not found. Download it from Google Cloud "
                    "Console (OAuth Client ID -> Desktop app) and place it in "
                    "this project folder. See README.md."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return creds


def send_email(to: str, subject: str, body: str) -> dict:
    """
    Sends a real email from the authenticated Google account.
    """
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        sent = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

        return {
            "status": "success",
            "message_id": sent.get("id"),
            "to": to,
            "subject": subject,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_calendar_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    attendees: list = None,
    description: str = "",
) -> dict:
    """
    Creates a real event on the user's primary Google Calendar.
    start_datetime / end_datetime must be ISO 8601, e.g. 2026-08-06T15:00:00
    If attendees are given, Google Calendar automatically emails them an invite.
    """
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        }
        if attendees:
            event["attendees"] = [{"email": a} for a in attendees]

        created = service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all",  # emails invites to attendees automatically
        ).execute()

        return {
            "status": "success",
            "event_id": created.get("id"),
            "link": created.get("htmlLink"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
