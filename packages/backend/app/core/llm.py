import json
from typing import AsyncGenerator
import httpx
from loguru import logger
from app.core.config import settings


class LLMService:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(
        self,
        messages: list[dict[str, str]],
        stream: bool = True,
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
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if chunk.get("done"):
                                break
                            if "message" in chunk:
                                yield chunk["message"].get("content", "")
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as e:
            logger.error(f"LLM request failed: {e}")
            yield f"\n\n_I encountered an error connecting to the LLM: {e}_"

    async def close(self):
        await self.client.aclose()
