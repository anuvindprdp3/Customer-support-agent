from __future__ import annotations

from collections import deque
from typing import Deque


class ConversationMemory:
    def __init__(self, max_turns: int = 6) -> None:
        self._max_turns = max_turns
        self._store: dict[str, Deque[dict]] = {}

    def add(self, session_id: str, role: str, content: str) -> None:
        history = self._store.setdefault(session_id, deque(maxlen=self._max_turns * 2))
        history.append({"role": role, "content": content})

    def get(self, session_id: str) -> list[dict]:
        return list(self._store.get(session_id, []))
