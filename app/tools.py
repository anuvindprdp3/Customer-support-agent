from __future__ import annotations

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "case_lookup",
                "description": "Look up a customer support case by case ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string"},
                    },
                    "required": ["case_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "schedule_appointment",
                "description": "Schedule a follow-up support appointment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "date": {"type": "string", "description": "YYYY-MM-DD"},
                        "time": {"type": "string", "description": "HH:MM"},
                        "reason": {"type": "string"},
                    },
                    "required": ["name", "email", "date", "time"],
                },
            },
        },
    ]


def run_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "case_lookup":
        case_id = arguments.get("case_id", "")
        return {
            "case_id": case_id,
            "status": "open",
            "priority": "normal",
            "last_update": "2026-01-08",
        }
    if name == "schedule_appointment":
        return {
            "confirmation_id": "APT-100045",
            "scheduled": True,
            **arguments,
        }
    return {"error": f"Unknown tool: {name}"}
