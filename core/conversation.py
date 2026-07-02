from __future__ import annotations
import uuid
import time
from models import Conversation, Message


class ConversationManager:
    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}
        self._active_id: str | None = None

    @property
    def active_id(self) -> str | None:
        return self._active_id

    def create(self, title: str = "New Conversation") -> str:
        conv_id = str(uuid.uuid4())
        now = time.time()
        self.conversations[conv_id] = Conversation(
            id=conv_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
        )
        self._active_id = conv_id
        return conv_id

    def set_active(self, conv_id: str) -> None:
        if conv_id in self.conversations:
            self._active_id = conv_id

    def add_message(self, conv_id: str, role: str, content: str) -> Message:
        msg = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=time.time(),
        )
        if conv_id in self.conversations:
            self.conversations[conv_id].messages.append(msg)
            self.conversations[conv_id].updated_at = time.time()
        return msg

    def get_messages(self, conv_id: str) -> list[dict]:
        if conv_id not in self.conversations:
            return []
        return [
            {"id": m.id, "role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in self.conversations[conv_id].messages
        ]

    def get_recent(self, limit: int = 20) -> list[dict]:
        sorted_convs = sorted(
            self.conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        return [
            {"id": c.id, "title": c.title, "created_at": c.created_at, "updated_at": c.updated_at}
            for c in sorted_convs[:limit]
        ]

    def delete(self, conv_id: str) -> None:
        self.conversations.pop(conv_id, None)
        if self._active_id == conv_id:
            self._active_id = None
