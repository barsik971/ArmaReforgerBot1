from core.base_plugin import BasePlugin
from loguru import logger
import threading
import time
import pyautogui
import numpy as np
from PIL import ImageGrab
import cv2

class AutoBandagePlugin(BasePlugin):
    def get_name(self):
        return "Автобинтування"

    def get_description(self):
        return "Виявляє червону область (поранення) і використовує бинт (4+R)"

    def on_enable(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        logger.info("AutoBandage enabled")

    def on_disable(self):
        self.running = False
        logger.info("AutoBandage disabled")

    def _monitor(self):
        while self.running:
            try:
                # Захоплюємо область центру екрану (приблизно де показник здоров'я)
                screen = np.array(ImageGrab.grab(bbox=(800, 400, 1120, 600)))
                # Перетворюємо в HSV для пошуку червоного
                hsv = cv2.cvtColor(screen, cv2.COLOR_RGB2HSV)
                lower_red1 = np.array([0, 100, 100])
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([160, 100, 100])
                upper_red2 = np.array([180, 255, 255])
                mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                mask = mask1 + mask2
                if np.sum(mask) > 500:  # Поріг червоних пікселів
                    # Натискаємо 4 (бинт) і утримуємо R 2.5 сек
                    pyautogui.press('4')
                    time.sleep(0.2)
                    pyautogui.keyDown('r')
                    time.sleep(2.5)
                    pyautogui.keyUp('r')
                    time.sleep(3)  # Затримка, щоб не спамити
            except Exception as e:
                logger.error(f"AutoBandage error: {e}")
            time.sleep(1)