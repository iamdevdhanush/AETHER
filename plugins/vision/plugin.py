"""
AETHER Vision Plugin
Image capture and analysis via OpenCV.
"""

import asyncio
import logging
import base64
import tempfile
import os
from pathlib import Path
from typing import Optional

from models.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class VisionPlugin(PluginBase):
    """
    Vision capabilities:
      - Capture from webcam via OpenCV
      - Analyze images via Ollama vision models
      - Screenshot capture
    """

    def initialize(self):
        self._cv2 = None
        self._ollama_url = "http://127.0.0.1:11434"
        self._vision_model = "llava"

        try:
            import cv2
            self._cv2 = cv2
            logger.info("OpenCV available")
        except ImportError:
            logger.warning("opencv-python not installed; vision capture disabled")

    async def execute(self, payload: dict) -> str:
        action = payload.get("action", "capture")
        text = payload.get("input", "Describe this image.").strip()
        image_path = payload.get("image_path", "")

        if action == "capture":
            return await self._capture_and_analyze(text)
        elif action == "analyze":
            if image_path and Path(image_path).exists():
                return await self._analyze_image(image_path, text)
            return "No image path provided."
        elif action == "screenshot":
            return await self._screenshot_and_analyze(text)
        elif action == "status":
            return self._status()
        else:
            return f"Unknown vision action: {action}"

    async def _capture_and_analyze(self, prompt: str) -> str:
        if self._cv2 is None:
            return "OpenCV not installed. Run: pip install opencv-python"

        try:
            cap = None
            loop = asyncio.get_event_loop()

            def _capture():
                cap = self._cv2.VideoCapture(0)
                if not cap.isOpened():
                    return None, "Cannot open camera"
                ret, frame = cap.read()
                cap.release()
                if not ret:
                    return None, "Failed to capture frame"
                return frame, None

            frame, error = await loop.run_in_executor(None, _capture)
            if error:
                return error

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name

            def _save(f, p):
                self._cv2.imwrite(p, f)

            await loop.run_in_executor(None, lambda: _save(frame, tmp_path))

            result = await self._analyze_image(tmp_path, prompt)
            os.unlink(tmp_path)
            return result

        except Exception as e:
            logger.error(f"Capture error: {e}", exc_info=True)
            return f"Vision capture error: {e}"

    async def _screenshot_and_analyze(self, prompt: str) -> str:
        try:
            import PIL.ImageGrab as ImageGrab
        except ImportError:
            return "Pillow not installed. Run: pip install Pillow"

        try:
            loop = asyncio.get_event_loop()

            def _take_screenshot():
                img = ImageGrab.grab()
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    img.save(tmp.name, "JPEG", quality=85)
                    return tmp.name

            tmp_path = await loop.run_in_executor(None, _take_screenshot)
            result = await self._analyze_image(tmp_path, prompt)
            os.unlink(tmp_path)
            return result

        except Exception as e:
            logger.error(f"Screenshot error: {e}", exc_info=True)
            return f"Screenshot error: {e}"

    async def _analyze_image(self, image_path: str, prompt: str) -> str:
        """Send image to Ollama vision model for analysis."""
        try:
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            return f"Failed to read image: {e}"

        try:
            import httpx
            payload = {
                "model": self._vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_b64],
                    }
                ],
                "stream": False,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._ollama_url}/api/chat",
                    json=payload,
                )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "No response")
            else:
                return (
                    f"Vision model not available. Ensure '{self._vision_model}' is installed: "
                    f"`ollama pull {self._vision_model}`\n"
                    f"Server response: {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Vision analysis error: {e}", exc_info=True)
            return f"Vision analysis error: {e}"

    def _status(self) -> str:
        cv_status = "✓ Available" if self._cv2 else "✗ Not installed (pip install opencv-python)"
        return (
            f"Vision Plugin Status\n"
            f"  OpenCV: {cv_status}\n"
            f"  Vision model: {self._vision_model}\n"
            f"  Ollama: {self._ollama_url}"
        )

    def shutdown(self):
        logger.info("Vision plugin shut down")

    def metadata(self) -> dict:
        return {
            "name": "vision",
            "description": "Webcam capture and AI image analysis via Ollama vision models",
            "version": "1.0.0",
            "icon": "👁️",
            "category": "ai",
        }

    def settings(self) -> dict:
        return {
            "vision_model": {
                "type": "str",
                "default": "llava",
                "description": "Ollama vision model name",
            },
            "camera_index": {
                "type": "int",
                "default": 0,
                "description": "Camera device index (0 = default)",
            },
        }
