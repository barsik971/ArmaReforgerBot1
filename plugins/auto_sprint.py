from core.base_plugin import BasePlugin
from loguru import logger
import threading
import time
import pyautogui

class AutoSprintPlugin(BasePlugin):
    def get_name(self):
        return "Автобіг"

    def get_description(self):
        return "Утримує Shift+W для бігу"

    def on_enable(self):
        self.running = True
        self.thread = threading.Thread(target=self._hold_sprint, daemon=True)
        self.thread.start()
        logger.info("AutoSprint enabled")

    def on_disable(self):
        self.running = False
        pyautogui.keyUp('shift')
        pyautogui.keyUp('w')
        logger.info("AutoSprint disabled")

    def _hold_sprint(self):
        while self.running:
            try:
                pyautogui.keyDown('shift')
                pyautogui.keyDown('w')
                time.sleep(60)
                pyautogui.keyUp('shift')
                pyautogui.keyUp('w')
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"AutoSprint error: {e}")