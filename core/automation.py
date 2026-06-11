import threading
import time
from loguru import logger
from core.game_controller import GameController
from core.plugin_manager import PluginManager
from core.adaptive_connector import AdaptiveConnector

class Automation:
    def __init__(self, config, game_controller, plugin_manager):
        self.config = config
        self.game_controller = game_controller
        self.plugin_manager = plugin_manager
        self.connector = AdaptiveConnector(config, game_controller)  # передаємо контролер
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("Automation started")

    def stop(self):
        self.running = False
        logger.info("Automation stopped")

    def _run(self):
        while self.running:
            try:
                # Запускаємо підключення, воно сама все зробить
                success = self.connector.connect()
                if success:
                    logger.info("Підключення успішне, чекаємо виходу з гри")
                    # Чекаємо, поки гра завершиться (процес зникне)
                    while self.running and self.game_controller.is_game_running():
                        time.sleep(10)
                else:
                    logger.warning("Спроба підключення не вдалася, пауза перед повторною спробою")
                    time.sleep(30)
            except Exception as e:
                logger.error(f"Automation error: {e}")
                time.sleep(30)