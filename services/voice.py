from __future__ import annotations
import asyncio
from typing import AsyncGenerator


class VoiceService:
    def __init__(self) -> None:
        self.is_listening = False
        self.audio_queue: asyncio.Queue[bytes] = asyncio.Queue()

    async def start_listening(self) -> None:
        self.is_listening = True

    async def stop_listening(self) -> None:
        self.is_listening = False

    async def process_audio(self, audio_data: bytes) -> str:
        # Placeholder — Faster Whisper integration planned
        await asyncio.sleep(0.1)
        return ""

    async def synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        # Placeholder — Piper TTS integration planned
        for _ in range(10):
            yield b"\x00" * 1024
            await asyncio.sleep(0.01)


voice_service = VoiceService()
