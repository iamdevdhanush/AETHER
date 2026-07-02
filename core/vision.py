from __future__ import annotations


class VisionService:
    def __init__(self) -> None:
        self._available = False

    async def initialize(self) -> None:
        try:
            import cv2
            self._available = True
        except ImportError:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def capture_screenshot(self) -> bytes | None:
        if not self._available:
            return None
        import cv2
        import numpy as np
        import pyautogui
        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode(".png", img)
        return buffer.tobytes()

    async def capture_camera(self) -> bytes | None:
        if not self._available:
            return None
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if ret:
            _, buffer = cv2.imencode(".jpg", frame)
            return buffer.tobytes()
        return None

    async def ocr(self, image_path: str) -> str:
        try:
            import pytesseract
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                return ""
            text = pytesseract.image_to_string(img)
            return text.strip()
        except ImportError:
            return "[OCR not available - install pytesseract]"
