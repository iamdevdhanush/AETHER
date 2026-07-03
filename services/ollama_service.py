"""
AETHER Ollama Service
Handles communication with local Ollama instance.
Supports streaming chat completions.
"""

import logging
import json
import asyncio
from typing import AsyncIterator, Optional

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2"
SYSTEM_PROMPT = """You are AETHER, an advanced AI assistant integrated into a native desktop environment.
You are helpful, precise, and thoughtful. You can assist with coding, analysis, writing, research, 
and system tasks. When given context from memory or previous conversations, use it naturally.
Keep responses clear and well-structured. Format code in markdown code blocks."""


class OllamaService:
    """
    Async client for the Ollama REST API.
    Supports streaming responses via httpx.
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.current_model = DEFAULT_MODEL
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(connect=5.0, read=120.0, write=10.0, pool=5.0),
            )
        return self._client

    def set_model(self, model_name: str):
        self.current_model = model_name
        logger.info(f"Model set to: {model_name}")

    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            client = self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Return list of locally available model names."""
        try:
            client = self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def stream_chat(
        self,
        messages: list[dict],
        memories: list[dict] = None,
        system_override: str = None,
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion from Ollama.
        Yields text chunks as they arrive.

        Args:
            messages: list of {"role": ..., "content": ...} dicts
            memories: relevant memory snippets to inject into system prompt
            system_override: optional system prompt override
        """
        system = system_override or SYSTEM_PROMPT

        if memories:
            memory_text = "\n".join(
                f"- {m['content']}" for m in memories[:10]
            )
            system += f"\n\nRelevant context from memory:\n{memory_text}"

        # Build ollama message list
        ollama_messages = [{"role": "system", "content": system}]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                ollama_messages.append({"role": role, "content": content})

        payload = {
            "model": self.current_model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_ctx": 4096,
            },
        }

        try:
            client = self._get_client()
            async with client.stream(
                "POST",
                "/api/chat",
                json=payload,
                timeout=httpx.Timeout(connect=5.0, read=120.0, write=10.0, pool=5.0),
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise RuntimeError(
                        f"Ollama returned {response.status_code}: {body.decode()}"
                    )

                async for line in response.aiter_lines():
                    raw = line.strip()
                    if not raw:
                        continue

                    try:
                        chunk_data = json.loads(raw)
                    except json.JSONDecodeError:
                        logger.warning("Ollama non-JSON line: %s", raw[:200])
                        continue

                    # Extract content BEFORE checking done — some Ollama versions
                    # send the final content token on the same chunk as done:true
                    content = ""
                    message = chunk_data.get("message")
                    if isinstance(message, dict):
                        content = message.get("content", "")
                    elif isinstance(message, str):
                        # Fallback: if message is a bare string, use it directly
                        content = message
                    elif "response" in chunk_data:
                        # Fallback: if using /api/generate format
                        content = chunk_data.get("response", "")

                    if chunk_data.get("done"):
                        # Yield any remaining content before closing
                        if content:
                            yield content
                        break

                    if content:
                        yield content

        except httpx.ConnectError:
            raise RuntimeError(
                "Cannot connect to Ollama. Please ensure Ollama is running: "
                "`ollama serve`"
            )
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise

    async def generate(self, prompt: str, system: str = None) -> str:
        """Non-streaming single generation."""
        result = ""
        messages = [{"role": "user", "content": prompt}]
        async for chunk in self.stream_chat(messages, system_override=system):
            result += chunk
        return result

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
