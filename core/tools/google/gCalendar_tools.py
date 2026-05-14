# core/tools/google/gCalendar_tools.py
from core.tools.google import gCalendarAPI

TOOL_MAP = {
    "create_event": gCalendarAPI.create_event,
    "list_events":  gCalendarAPI.list_events,
    "delete_event": gCalendarAPI.delete_event,
}

gCalendar_TOOLS = [
    {
        "name": "create_event",
        "description": "Create a Google Calendar event. Infer end time if not given (default 1 hour).",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":    {"type": "string", "description": "Event title e.g. 'Gym'"},
                "start":    {"type": "string", "description": "ISO 8601 e.g. 2026-05-01T10:00:00"},
                "end":      {"type": "string", "description": "ISO 8601 e.g. 2026-05-01T11:00:00"},
                "timezone": {"type": "string", "description": "IANA timezone. Default America/Los_Angeles."},
                "color":    {"type": "string", "description": "Color ID for the event (1-11). If not specified, defaults to 1 (blue)."}
            },
            "required": ["title", "start", "end"]
        }
    },
    {
        "name": "list_events",
        "description": "List upcoming calendar events with their IDs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "Days ahead to look. Default 7."}
            },
            "required": []
        }
    },
    {
        "name": "delete_event",
        "description": "Delete a calendar event by ID. Requires event ID from a list_events call.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Google Calendar event ID."}
            },
            "required": ["event_id"]
        }
    }
]