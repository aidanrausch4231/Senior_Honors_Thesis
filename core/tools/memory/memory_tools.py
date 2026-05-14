# core/tools/memory/memory_tools.py
from core.tools.memory.memoryAPI import (
    read_shortTerm,
    read_midTerm,
    read_longTerm,
    update_shortTerm,
    update_midTerm,
    update_longTerm,
)

MEMORY_TOOL_MAP = {
    "read_shortTerm":   read_shortTerm,
    "read_midTerm":     read_midTerm,
    "read_longTerm":    read_longTerm,
    "update_shortTerm": update_shortTerm,
    "update_midTerm":   update_midTerm,
    "update_longTerm":  update_longTerm,
}

MEMORY_TOOLS = [
    {
        "name": "read_shortTerm",
        "description": "Read shortTerm.md. Use when current goals, focus, or recent context is needed.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "read_midTerm",
        "description": "Read midTerm.md. Use when active projects or 3-6 month goals are needed.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "read_longTerm",
        "description": "Read longTerm.md. Use when core identity or background context is needed. Use sparingly.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "update_shortTerm",
        "description": "Update a section in shortTerm.md. Use when goals, focus, mood, or notes change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {"type": "string", "description": "Exact ## section header e.g. 'Active Goals (This Week)'"},
                "content": {"type": "string", "description": "New content for the section. No header needed."}
            },
            "required": ["section", "content"]
        }
    },
    {
        "name": "update_midTerm",
        "description": "Update a section in midTerm.md. Use when a project ships or goals shift. Roughly monthly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {"type": "string", "description": "Exact ## section header."},
                "content": {"type": "string", "description": "New content for the section."}
            },
            "required": ["section", "content"]
        }
    },
    {
        "name": "update_longTerm",
        "description": "Update a section in longTerm.md. Rarely used — only when core identity shifts. Requires explicit user confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {"type": "string", "description": "Exact ## section header."},
                "content": {"type": "string", "description": "New content for the section."},
                "confirm": {"type": "boolean", "description": "Must be true. Only pass after explicit user confirmation."}
            },
            "required": ["section", "content", "confirm"]
        }
    }
]