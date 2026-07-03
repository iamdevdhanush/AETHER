"""
AETHER Voice Plugin
Speech-to-text via Faster Whisper, text-to-speech via Piper TTS.
"""

import asyncio
import logging
import io
import tempfile
import os
import sys
from pathlib import Path
from typing import Optional

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class VoicePlugin(PluginBase):
    """
    Voice capabilities:
      - STT: Record microphone → Faster Whisper → text
      - TTS: Text → Piper TTS → audio playback
    """

    def initialize(self):
        self._whisper_model = None
        self._piper_available = False
        self._piper_model_path: Optional[Path] = None
        self._recording = False

        # Attempt to load Faster Whisper
        try:
            from faster_whisper import WhisperModel
            self._WhisperModel = WhisperModel
            logger.info("Faster Whisper available")
        except ImportError:
            self._WhisperModel = None
            logger.warning("faster-whisper not installed; STT disabled")

        # Check for Piper
        self._piper_exe = self._find_piper()
        if self._piper_exe:
            self._piper_available = True
            logger.info(f"Piper TTS found: {self._piper_exe}")
        else:
            logger.warning("Piper TTS not found; TTS disabled")

    def _find_piper(self) -> Optional[str]:
        """Locate piper executable."""
        from shutil import which
        if sys.platform == "win32":
            candidates = [
                Path.home() / "AppData" / "Local" / "piper" / "piper.exe",
                Path("C:/piper/piper.exe"),
            ]
            for c in candidates:
                if c.exists():
                    return str(c)
        else:
            path = which("piper")
            if path:
                return path
            for p in [Path("/usr/local/bin/piper"), Path(Path.home() / ".local/bin/piper")]:
                if p.exists():
                    return str(p)
        return None

    def _ensure_whisper_loaded(self):
        """Lazy-load Whisper model on first use."""
        if self._whisper_model is None and self._WhisperModel is not None:
            logger.info("Loading Whisper model (tiny)...")
            self._whisper_model = self._WhisperModel(
                "tiny",
                device="cpu",
                compute_type="int8",
            )
            logger.info("Whisper model loaded")

    async def execute(self, payload: dict) -> str:
        action = payload.get("action", "tts")
        text = payload.get("input", "").strip()

        if action == "tts":
            return await self._speak(text)
        elif action == "stt":
            audio_path = payload.get("audio_path", "")
            return await self._transcribe(audio_path)
        elif action == "record":
            return await self._record_and_transcribe()
        elif action == "status":
            return self._status()
        else:
            return f"Unknown voice action: {action}"

    async def _speak(self, text: str) -> str:
        if not text:
            return "No text to speak."

        if not self._piper_available:
            return "Piper TTS not available. Install from https://github.com/rhasspy/piper"

        model_path = self._piper_model_path
        if not model_path:
            return (
                "No Piper voice model configured. "
                "Download a model from https://huggingface.co/rhasspy/piper-voices"
            )

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            cmd = [
                self._piper_exe,
                "--model", str(model_path),
                "--output_file", tmp_path,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate(input=text.encode("utf-8"))

            if proc.returncode != 0:
                return f"Piper TTS error: {stderr.decode()}"

            # Play the audio
            await self._play_audio(tmp_path)
            os.unlink(tmp_path)
            return f"Spoke: {text[:60]}..."

        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)
            return f"TTS error: {e}"

    async def _play_audio(self, wav_path: str):
        """Play a WAV file using the platform audio player."""
        try:
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
            elif sys.platform == "darwin":
                proc = await asyncio.create_subprocess_exec(
                    "afplay", wav_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
            else:
                # Linux: try multiple players
                for player in ("aplay", "paplay", "ffplay"):
                    from shutil import which
                    if which(player):
                        args = [player, wav_path]
                        if player == "ffplay":
                            args = ["ffplay", "-nodisp", "-autoexit", wav_path]
                        proc = await asyncio.create_subprocess_exec(
                            *args,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL,
                        )
                        await proc.wait()
                        break
        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    async def _transcribe(self, audio_path: str) -> str:
        if not audio_path or not Path(audio_path).exists():
            return f"Audio file not found: {audio_path}"

        try:
            self._ensure_whisper_loaded()
        except Exception as e:
            return f"Failed to load Whisper: {e}"

        if self._whisper_model is None:
            return "Faster Whisper not installed. Run: pip install faster-whisper"

        try:
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                lambda: self._whisper_model.transcribe(audio_path, language="en"),
            )
            text = " ".join(seg.text.strip() for seg in segments)
            return text.strip() if text.strip() else "(silence or inaudible)"
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return f"Transcription failed: {e}"

    async def _record_and_transcribe(self) -> str:
        """Record 5 seconds from microphone and transcribe."""
        try:
            import sounddevice as sd
            import numpy as np
            import scipy.io.wavfile as wavfile
        except ImportError:
            return "sounddevice/scipy not installed. Run: pip install sounddevice scipy"

        try:
            sample_rate = 16000
            duration = 5  # seconds

            logger.info("Recording audio...")
            recording = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: sd.rec(
                    int(duration * sample_rate),
                    samplerate=sample_rate,
                    channels=1,
                    dtype="float32",
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, sd.wait)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            audio_int16 = (recording * 32767).astype("int16")
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: wavfile.write(tmp_path, sample_rate, audio_int16),
            )

            result = await self._transcribe(tmp_path)
            os.unlink(tmp_path)
            return result

        except Exception as e:
            logger.error(f"Recording error: {e}", exc_info=True)
            return f"Recording failed: {e}"

    def _status(self) -> str:
        whisper_status = "✓ Available" if self._WhisperModel else "✗ Not installed"
        piper_status = f"✓ {self._piper_exe}" if self._piper_available else "✗ Not found"
        model_status = str(self._piper_model_path) if self._piper_model_path else "Not configured"
        return (
            f"Voice Plugin Status\n"
            f"  STT (Faster Whisper): {whisper_status}\n"
            f"  TTS (Piper): {piper_status}\n"
            f"  Piper model: {model_status}"
        )

    def shutdown(self):
        self._whisper_model = None
        logger.info("Voice plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "voice",
            "description": "Speech-to-text (Faster Whisper) and text-to-speech (Piper TTS)",
            "version": "1.0.0",
            "icon": "🎙️",
            "category": "ai",
        }

    def settings(self) -> dict:
        return {
            "whisper_model": {
                "type": "str",
                "default": "tiny",
                "description": "Whisper model size: tiny, base, small, medium, large",
            },
            "piper_model_path": {
                "type": "str",
                "default": "",
                "description": "Path to Piper voice model (.onnx file)",
            },
            "record_duration": {
                "type": "int",
                "default": 5,
                "description": "Recording duration in seconds",
            },
        }
