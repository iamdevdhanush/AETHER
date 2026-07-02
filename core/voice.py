from __future__ import annotations
from typing import AsyncGenerator
from services.voice import VoiceService


class VoiceCoordinator:
    def __init__(self, voice_service: VoiceService) -> None:
        self.service = voice_service
        self._is_listening = False

    @property
    def is_listening(self) -> bool:
        return self._is_listening

    async def start_listening(self) -> None:
        await self.service.start_listening()
        self._is_listening = True

    async def stop_listening(self) -> None:
        await self.service.stop_listening()
        self._is_listening = False

    async def transcribe(self, audio_data: bytes) -> str:
        return await self.service.process_audio(audio_data)

    async def speak(self, text: str) -> AsyncGenerator[bytes, None]:
        async for chunk in self.service.synthesize(text):
            yield chunk
