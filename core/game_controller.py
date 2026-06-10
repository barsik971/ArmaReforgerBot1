import pyautogui
import pytesseract
from PIL import ImageGrab
import time
from loguru import logger

class GameController:
    def __init__(self, config):
        self.config = config

    def get_game_state(self) -> str:
        try:
            # Перевіряємо, чи доступний tesseract
            if not self._tesseract_available():
                return "unknown"
            screen = ImageGrab.grab()
            text = pytesseract.image_to_string(screen, lang='eng').lower()
            if "main menu" in text:
                return "main_menu"
            if "multiplayer" in text and "favorites" not in text:
                return "multiplayer"
            if "favorites" in text:
                return "favorites"
            if "server browser" in text or "servers" in text:
                return "server_list"
            if "queue" in text and "position" in text:
                return "queue"
            if "deploy" in text or "spawn" in text:
                return "in_game"
            return "unknown"
        except Exception as e:
            logger.error(f"get_game_state error: {e}")
            return "unknown"

    def _tesseract_available(self):
        import subprocess
        try:
            subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
            return True
        except:
            return False

    def click_filter_positions(self):
        positions = self.config.get("filter_positions", [])
        for x, y in positions:
            pyautogui.click(x, y)
            time.sleep(0.1)
        logger.info("Filters toggled")

    def connect_to_server(self, server_name: str):
        # Заглушка: реальна логіка має шукати сервер через OCR
        pass

    def is_queue_below_threshold(self, threshold: int) -> bool:
        try:
            screen = ImageGrab.grab()
            text = pytesseract.image_to_string(screen, lang='eng')
            import re
            match = re.search(r'queue:\s*(\d+)', text, re.IGNORECASE)
            if match:
                return int(match.group(1)) <= threshold
        except:
            pass
        return False

    def get_queue_position(self) -> int:
        try:
            screen = ImageGrab.grab()
            text = pytesseract.image_to_string(screen, lang='eng')
            import re
            match = re.search(r'queue:\s*(\d+)', text, re.IGNORECASE)
            return int(match.group(1)) if match else 999
        except:
            return 999