# core/calendar.py
import os
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
import threading
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/gmail.modify",
]
#different gmail accounts
ACCOUNTS = {
    "personal": {
        "token":       "config/token_personal.json",
        "credentials": "config/credentials_personal.json",
    },
}

_creds = None
_services = {}


def authorize(account: str):
    account = ACCOUNTS[account]
    creds = None

    if os.path.exists(account['token']):
        try: 
            creds = Credentials.from_authorized_user_file(account['token'], SCOPES)
        except Exception as e:
                print(e)


    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(account['credentials'], SCOPES)
            creds = flow.run_local_server(port=0)

        with open(account['token'], "w") as f:
            f.write(creds.to_json())

    creds = creds
    return creds


def get_service():
    token_file = os.path.join('config', 'token_personal.json')
    if not os.path.exists(token_file):
        raise FileNotFoundError(f"Run auth script first to generate {token_file} ")
    creds = Credentials.from_authorized_user_file(token_file)
    return build('calendar', 'v3', credentials=creds)

def create_event(title: str, start: str, end: str, timezone: str = "America/Los_Angeles", color: str = None):
    service = get_service()
    event = {
        'summary': title,
        'start': {'dateTime': start, 'timeZone': timezone},
        'end': {'dateTime': end, 'timeZone': timezone}
    }
    if color:
        event['colorId'] = color
    elif 'building' in title.lower():
        event['colorId'] = '6'  # Orange for building events
    result = service.events().insert(calendarId='primary', body=event).execute()
    return f"Created: {result.get('htmlLink')}"

def list_events(days_ahead: int = 7):
    service = get_service()
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    res = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = res.get('items', [])
    if not events:
        return f"No events in the next {days_ahead} days."

    lines = [f"Upcoming events ({days_ahead} days):"]
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        dt = datetime.fromisoformat(start)
        lines.append(f"- ID: {e['id']} | {dt.strftime('%a %b %d, %I:%M %p')}: {e['summary']}")

    return "\n".join(lines)

def delete_event(event_id: str):
    get_service().events().delete(calendarId='primary', eventId=event_id).execute()
    return "Event deleted."