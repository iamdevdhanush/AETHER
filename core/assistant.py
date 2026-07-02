from __future__ import annotations
from typing import AsyncGenerator
from services.ollama import LLMService
from core.conversation import ConversationManager
from core.memory import MemoryManager
from core.execution import ExecutionTracker
from models import AICoreState


class Assistant:
    def __init__(
        self,
        llm: LLMService,
        conversation_manager: ConversationManager,
        memory_manager: MemoryManager,
        execution_tracker: ExecutionTracker,
    ) -> None:
        self.llm = llm
        self.conversations = conversation_manager
        self.memory = memory_manager
        self.execution = execution_tracker
        self.state: AICoreState = AICoreState.idle

    def set_state(self, state: AICoreState) -> None:
        self.state = state

    async def process_message(
        self, content: str, conversation_id: str | None = None
    ) -> AsyncGenerator[str, None]:
        self.set_state(AICoreState.thinking)

        conv_id = conversation_id or self.conversations.create()
        self.conversations.add_message(conv_id, "user", content)

        messages = self.conversations.get_messages(conv_id)
        system_prompt = {
            "role": "system",
            "content": "You are AETHER, an advanced AI operating system. "
                       "You assist the user with tasks, conversation, automation, and system control. "
                       "Be concise, helpful, and precise.",
        }
        llm_messages = [system_prompt] + [
            {"role": m["role"], "content": m["content"]} for m in messages[:-1]
        ]

        response_content = ""
        async for chunk in self.llm.generate(llm_messages, stream=True):
            response_content += chunk
            yield chunk

        self.conversations.add_message(conv_id, "assistant", response_content)
        await self.memory.save(f"User: {content}\nAETHER: {response_content}")
        self.set_state(AICoreState.idle)

    async def process_message_non_streaming(
        self, content: str, conversation_id: str | None = None
    ) -> str:
        self.set_state(AICoreState.thinking)
        conv_id = conversation_id or self.conversations.create()
        self.conversations.add_message(conv_id, "user", content)

        messages = self.conversations.get_messages(conv_id)
        system_prompt = {
            "role": "system",
            "content": "You are AETHER, an advanced AI operating system.",
        }
        llm_messages = [system_prompt] + [
            {"role": m["role"], "content": m["content"]} for m in messages[:-1]
        ]

        response = await self.llm.generate_non_streaming(llm_messages)
        self.conversations.add_message(conv_id, "assistant", response)
        await self.memory.save(f"User: {content}\nAETHER: {response}")
        self.set_state(AICoreState.idle)
        return response
