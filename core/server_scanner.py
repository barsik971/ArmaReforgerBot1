import time
import pyautogui
import pytesseract
from PIL import ImageGrab
import cv2
import numpy as np
import re
from pathlib import Path
from loguru import logger

class ServerScanner:
    """Сканує список серверів у грі та витягує інформацію про них."""

    def __init__(self, config):
        self.config = config
        self.server_list_region = config.get("server_list_region", (0, 150, 1920, 900))
        self.scroll_amount = config.get("scroll_amount", -5)
        self.scroll_pause = 0.5
        self.max_scroll_attempts = config.get("max_scroll_attempts", 20)
        self.refresh_key = config.get("refresh_key", "r")
        self.templates_dir = Path("training_data/templates")
        self.assets_dir = Path("assets")

    def refresh_list(self):
        """Натискає клавішу оновлення списку."""
        pyautogui.press(self.refresh_key)
        time.sleep(2)

    def find_server_info(self, server_name, max_scroll=None):
        """
        Шукає сервер за назвою у списку (з прокруткою) і повертає (players, max_players, queue)
        або (None, None, None) якщо не знайдено.
        """
        attempts = max_scroll if max_scroll is not None else self.max_scroll_attempts
        for _ in range(attempts):
            screen = ImageGrab.grab(bbox=self.server_list_region)
            text = pytesseract.image_to_string(screen, lang='eng')
            if server_name.lower() in text.lower():
                # Сервер знайдено, спробуємо розпарсити
                info = self._parse_server_info(text, server_name)
                if info:
                    return info
            pyautogui.scroll(self.scroll_amount)
            time.sleep(self.scroll_pause)
        return (None, None, None)

    def find_server_position(self, server_name):
        """Повертає (x, y) центру рядка сервера або None."""
        # Спочатку пробуємо шаблон (якщо є)
        for directory in (self.templates_dir, self.assets_dir):
            path = directory / f"{server_name.lower().replace(' ', '_')}.png"
            if path.exists():
                rect = self._find_image_on_screen(str(path), confidence=0.8)
                if rect:
                    return (rect[0] + rect[2]//2, rect[1] + rect[3]//2)
        # Потім OCR
        return self._ocr_find_word(server_name, region=self.server_list_region)

    def _parse_server_info(self, text, server_name):
        """Витягує кількість гравців і чергу з тексту, що містить назву сервера."""
        for line in text.split('\n'):
            if server_name.lower() in line.lower():
                nums = re.findall(r'(\d+)', line)
                if len(nums) >= 2:
                    try:
                        players = int(nums[-2])
                        max_players = int(nums[-1])
                        queue_match = re.search(r'\(\+(\d+)\)', line)
                        queue = int(queue_match.group(1)) if queue_match else 0
                        return (players, max_players, queue)
                    except ValueError:
                        pass
        return None

    def _ocr_find_word(self, word, region=None):
        img = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        for i, text in enumerate(data['text']):
            if word.lower() in text.lower():
                x = data['left'][i] + data['width'][i] // 2
                y = data['top'][i] + data['height'][i] // 2
                if region:
                    x += region[0]
                    y += region[1]
                return (x, y)
        return None

    def _find_image_on_screen(self, image_path, confidence=0.8, region=None):
        try:
            screen = np.array(ImageGrab.grab(bbox=region)) if region else np.array(ImageGrab.grab())
            template = cv2.imread(image_path)
            if template is None:
                return None
            h, w = template.shape[:2]
            res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val >= confidence:
                return (max_loc[0], max_loc[1], w, h)
        except Exception as e:
            logger.error(f"Image match error: {e}")
        return None