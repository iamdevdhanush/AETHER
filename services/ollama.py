from __future__ import annotations
import json
import httpx
from typing import AsyncGenerator
from services.config import settings


class LLMService:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self._client = httpx.AsyncClient(timeout=120.0)

    async def generate(
        self, messages: list[dict[str, str]], stream: bool = True
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }
        try:
            async with self._client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break
        except Exception as e:
            yield f"\n\n[Error communicating with Ollama: {e}]"

    async def generate_non_streaming(
        self, messages: list[dict[str, str]]
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }
        try:
            response = await self._client.post(
                f"{self.base_url}/api/chat", json=payload
            )
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            return f"[Error communicating with Ollama: {e}]"

    async def close(self) -> None:
        await self._client.aclose()
