"""
AETHER Conversation Service
Manages conversation lifecycle and message persistence.
Supports rename, delete (cascade), duplicate, export, search, and auto-title.
"""

import logging
import json
import re
from datetime import datetime, timezone
from typing import Optional

from database.db_manager import DatabaseManager
from services.ollama_service import OllamaService
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 32

# Phrases to strip from the beginning of a message when generating a title.
STRIP_PREFIXES = re.compile(
    r"^(help me\s+(to\s+)?|can you\s+|could you\s+|would you\s+|"
    r"i need\s+(to\s+|you\s+to\s+)?|i want\s+(to\s+|you\s+to\s+)?|"
    r"please\s+|tell me\s+(how\s+to\s+)?|show me\s+(how\s+to\s+)?|"
    r"i'd like\s+(to\s+|you\s+to\s+)?|i would like\s+(to\s+|you\s+to\s+)?)",
    re.I,
)


class ConversationService:
    """
    Business logic layer for conversations.
    Wraps database operations and handles title generation.
    """

    def __init__(self, db: DatabaseManager, ollama: OllamaService,
                 memory: MemoryService):
        self.db = db
        self.ollama = ollama
        self.memory = memory

    async def create_conversation(self, title: str = "New Conversation",
                                   model: str = None) -> dict:
        """Create a new conversation and return its metadata."""
        model = model or self.ollama.current_model
        conv = self.db.create_conversation(title=title, model=model)
        logger.info("Created conversation %s: %s", conv["id"][:8], title)
        return conv

    async def list_conversations(self) -> list[dict]:
        """Return all non-archived conversations, newest first."""
        return self.db.list_conversations()

    async def get_conversation(self, conv_id: str) -> Optional[dict]:
        return self.db.get_conversation(conv_id)

    async def rename_conversation(self, conv_id: str, new_title: str) -> bool:
        """Rename a conversation. Persists to SQLite immediately."""
        new_title = new_title.strip()[:64]
        if not new_title:
            return False
        self.db.rename_conversation(conv_id, new_title)
        logger.info("Renamed conversation %s: %s", conv_id[:8], new_title)
        return True

    async def delete_conversation(self, conv_id: str):
        """
        Cascade delete:
          - Conversation record
          - All messages
          - Timeline events for this conversation
          - Memory references (set conversation_id to NULL)
        """
        self.db.delete_conversation(conv_id)
        logger.info("Deleted conversation %s (cascade)", conv_id[:8])

    async def duplicate_conversation(self, conv_id: str) -> Optional[dict]:
        """Duplicate a conversation with all messages. Returns new conv metadata."""
        original = await self.get_conversation(conv_id)
        if not original:
            return None
        base_title = original["title"][:56] + " (copy)"
        new_conv = self.db.duplicate_conversation(conv_id, base_title)
        if new_conv:
            logger.info("Duplicated conversation %s -> %s: %s",
                         conv_id[:8], new_conv["id"][:8], base_title)
        return new_conv

    async def add_message(self, conversation_id: str, role: str,
                           content: str) -> dict:
        """Persist a message and auto-generate title from first user message."""
        msg = self.db.add_message(conversation_id, role, content)

        if role == "user":
            conv = self.db.get_conversation(conversation_id)
            is_first_user_msg = conv and conv.get("message_count", 0) <= 1
            if is_first_user_msg and not conv.get("custom_title", 0):
                title = self._generate_title(content)
                self.db.set_conversation_title(conversation_id, title)
                logger.info("Auto-generated title for %s: %s",
                             conversation_id[:8], title)
        return msg

    async def get_messages(self, conversation_id: str) -> list[dict]:
        """Return all messages for a conversation."""
        return self.db.get_messages(conversation_id)

    async def search_conversations(self, query: str) -> list[dict]:
        """Search conversations by title or message content."""
        query = query.strip()
        if not query:
            return self.db.list_conversations()
        return self.db.search_conversations_by_content(query)

    async def export_conversation_markdown(self, conv_id: str) -> str:
        """Export conversation as Markdown. Returns the markdown string."""
        conv = await self.get_conversation(conv_id)
        messages = await self.get_messages(conv_id)
        timeline = self.db.get_conversation_timeline_events(conv_id)

        lines = [
            f"# {conv['title']}",
            "",
            f"*Exported: {datetime.now(timezone.utc).isoformat()}*",
            f"*Model: {conv.get('model', 'unknown')}*",
            f"*Messages: {len(messages)}*",
            f"*Created: {conv.get('created_at', 'unknown')}*",
            "",
            "---",
            "",
        ]
        for msg in messages:
            role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙", "error": "⚠"}.get(
                msg["role"], "💬")
            lines.append(f"### {role_icon} **{msg['role'].title()}**")
            lines.append("")
            lines.append(msg["content"])
            lines.append("")

        if timeline:
            lines.extend(["", "---", "", "## Execution Timeline", ""])
            for ev in timeline:
                lines.append(f"- **{ev['event_type']}**: {ev['description']}")

        return "\n".join(lines)

    async def export_conversation_json(self, conv_id: str) -> str:
        """Export conversation as JSON. Returns the JSON string."""
        conv = await self.get_conversation(conv_id)
        messages = await self.get_messages(conv_id)
        timeline = self.db.get_conversation_timeline_events(conv_id)

        export = {
            "title": conv["title"],
            "model": conv.get("model", "unknown"),
            "created_at": conv.get("created_at", ""),
            "updated_at": conv.get("updated_at", ""),
            "message_count": len(messages),
            "messages": [
                {
                    "role": m["role"],
                    "content": m["content"],
                    "created_at": m["created_at"],
                }
                for m in messages
            ],
            "execution_timeline": [
                {
                    "type": ev["event_type"],
                    "description": ev["description"],
                    "created_at": ev["created_at"],
                }
                for ev in timeline
            ],
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }
        return json.dumps(export, indent=2, ensure_ascii=False)

    async def get_context_window(self, conversation_id: str,
                                  max_messages: int = 20) -> list[dict]:
        """Get the most recent messages for context."""
        messages = self.db.get_messages(conversation_id)
        return messages[-max_messages:]

    # ── Title Generation ──────────────────────────────────────────────────

    def _generate_title(self, first_message: str) -> str:
        """
        Generate a concise title from the user's first message.

        Rules:
          - Strip polite prefixes ("Help me", "Can you", etc.) iteratively
          - Expand contractions (What's -> What is) for noun extraction
          - For questions, extract the core noun/subject
          - Capitalize first letter
          - Max 32 characters, truncate with "..." if longer
        """
        title = first_message.strip()
        if not title:
            return "New Conversation"

        # Iteratively strip polite prefixes
        prev = None
        while prev != title:
            prev = title
            title = STRIP_PREFIXES.sub("", title).strip()
        title = title.replace("\n", " ").replace("\r", "")

        while "  " in title:
            title = title.replace("  ", " ")

        title = title.strip(" '\"`.,!?;:")
        if not title:
            return "New Conversation"

        # Check if the ORIGINAL stripped form was a question
        # We preserve the ? through the prefix stripping but it got removed
        # above. Let's re-check the original cleaned title.
        had_question = "?" in first_message

        # Try to extract core noun from questions
        words = title.split()
        max_q_words = ("what", "how", "why", "when", "where", "who")
        skip_words = ("is", "are", "was", "were", "does", "do", "can",
                      "would", "could", "should", "will", "shall",
                      "the", "a", "an", "my", "your", "this", "that")

        if had_question and len(words) >= 2:
            first_word = words[0].lower().replace("'s", "").replace("'re", "").replace("'ve", "")
            if first_word in max_q_words:
                expanded_text = title.lower().replace("what's", "what is").replace("how's", "how is")
                words = expanded_text.split()

                noun_idx = 1
                while noun_idx < len(words) and words[noun_idx] in skip_words:
                    noun_idx += 1

                if noun_idx < len(words):
                    extracted = " ".join(words[noun_idx:]).strip()
                    if len(extracted) < len(title) * 0.8:
                        title = extracted

        # Final cleanup
        title = title.strip(" '\"`.,!?;:")
        if not title:
            return "New Conversation"
        title = title[0].upper() + title[1:] if title else title

        if len(title) > MAX_TITLE_LENGTH:
            title = title[:MAX_TITLE_LENGTH - 3].rstrip() + "..."

        return title if title else "New Conversation"
