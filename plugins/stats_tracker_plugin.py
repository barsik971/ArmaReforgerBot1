from core.base_plugin import BasePlugin
from loguru import logger
import threading
import time
import pytesseract
from PIL import ImageGrab
import re
from core.stats_tracker import StatsTracker

class StatsTrackerPlugin(BasePlugin):
    def get_name(self):
        return "Запис статистики бою"

    def get_description(self):
        return "Зчитує kills, deaths, score з екрану та зберігає в JSON"

    def on_enable(self):
        self.tracker = StatsTracker()
        self.running = True
        self.thread = threading.Thread(target=self._track, daemon=True)
        self.thread.start()
        logger.info("Stats tracker enabled")

    def on_disable(self):
        self.running = False
        logger.info("Stats tracker disabled")

    def _track(self):
        while self.running:
            try:
                # Припускаємо область таблиці результатів (потрібно калібрування)
                img = ImageGrab.grab(bbox=(800, 500, 1100, 650))
                text = pytesseract.image_to_string(img, lang='eng')
                kills = re.search(r'Kills:\s*(\d+)', text)
                deaths = re.search(r'Deaths:\s*(\d+)', text)
                score = re.search(r'Score:\s*(\d+)', text)
                if kills and deaths and score:
                    self.tracker.add_record(
                        int(kills.group(1)),
                        int(deaths.group(1)),
                        int(score.group(1))
                    )
            except Exception as e:
                logger.error(f"Stats tracker error: {e}")
            time.sleep(10)