from core.base_plugin import BasePlugin
from loguru import logger
import threading
import time
import pyautogui
import pytesseract
from PIL import ImageGrab

class AutoReloadPlugin(BasePlugin):
    def get_name(self):
        return "Автоперезарядка"

    def get_description(self):
        return "Сканує екран на текст 'out of ammo' і натискає R"

    def on_enable(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        logger.info("AutoReloadPlugin enabled")

    def on_disable(self):
        self.running = False
        logger.info("AutoReloadPlugin disabled")

    def _monitor(self):
        while self.running:
            try:
                # Зменшуємо область для прискорення
                img = ImageGrab.grab(bbox=(0, 0, 1920, 200))  # верхня частина екрану
                text = pytesseract.image_to_string(img, lang='eng')
                if "out of ammo" in text.lower() or "reload" in text.lower():
                    pyautogui.press('r')
                    time.sleep(1)
            except Exception as e:
                logger.error(f"AutoReload error: {e}")
            time.sleep(0.5)