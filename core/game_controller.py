import pyautogui
import pytesseract
from PIL import ImageGrab, Image
import cv2
import numpy as np
import time
from loguru import logger

class GameController:
    def __init__(self, config):
        self.config = config
        # Регіони для OCR можна налаштувати через калібрування
        self.regions = {}
        self.load_calibration()

    def load_calibration(self):
        # Заглушка – у реальному проєкті зберігати координати
        pass

    def find_game_window(self):
        # Пошук вікна ArmaReforger (можна через pygetwindow)
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle('Arma Reforger')
            if windows:
                return windows[0]
        except ImportError:
            pass
        return None

    def get_game_state(self) -> str:
        """Визначає стан гри за допомогою OCR."""
        # Отримуємо скріншот і шукаємо характерні слова
        screen = ImageGrab.grab()
        text = pytesseract.image_to_string(screen, lang='eng').lower()
        if "arma reforger" not in text and "multiplayer" not in text:
            return "not_running"
        if "main menu" in text or "play" in text:
            return "main_menu"
        if "multiplayer" in text or "server browser" in text or "servers" in text:
            return "server_list"
        if "queue" in text and "position" in text:
            return "faction_queue"
        if "deploy" in text or "spawn" in text or "respawn" in text:
            return "in_game"
        return "unknown"

    def click_filter_positions(self):
        # Вимкнення фільтрів за заданими координатами
        positions = self.config.get("filter_positions", [])
        for x, y in positions:
            pyautogui.click(x, y)
            time.sleep(0.1)
        logger.info("Filters toggled")

    def connect_to_server(self, server_name: str):
        # Натискання кнопок для підключення (спрощено)
        # У реальності потрібно більш складне розпізнавання
        pass

    def is_queue_below_threshold(self, threshold: int) -> bool:
        # Розпізнати поточну чергу
        screen = ImageGrab.grab()
        text = pytesseract.image_to_string(screen, lang='eng')
        import re
        match = re.search(r'queue:\s*(\d+)', text, re.IGNORECASE)
        if match:
            queue = int(match.group(1))
            return queue <= threshold
        return False

    def get_queue_position(self) -> int:
        # Повертає номер у черзі
        screen = ImageGrab.grab()
        text = pytesseract.image_to_string(screen, lang='eng')
        import re
        match = re.search(r'queue:\s*(\d+)', text, re.IGNORECASE)
        return int(match.group(1)) if match else 999