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
        self.connector = AdaptiveConnector(config)   # тепер Adaptive
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
                state = self.game_controller.get_game_state()
                logger.debug(f"Game state: {state}")
                if state == "not_running":
                    logger.warning("Гра не запущена")
                elif state in ("main_menu", "multiplayer", "favorites", "server_list"):
                    self.connector.connect()
                    # Після успішного підключення чекаємо виходу з гри
                    while self.running and self.game_controller.get_game_state() == "in_game":
                        time.sleep(10)
                time.sleep(5)
            except Exception as e:
                logger.error(f"Automation error: {e}")
                time.sleep(10)