from __future__ import annotations

INJECTION_MARKERS = [
    "ignore previous",
    "system prompt",
    "developer message",
    "bypass",
    "jailbreak",
]


def check_input(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    if any(marker in lowered for marker in INJECTION_MARKERS):
        return False, "I can't help with that request. Please ask a support question."
    return True, ""


def check_output(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    if "api key" in lowered or "password" in lowered:
        return False, "I can't share sensitive data."
    return True, ""
