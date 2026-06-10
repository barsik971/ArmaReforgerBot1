import threading
import time
from loguru import logger
from core.server_connector import ServerConnector

class Automation:
    def __init__(self, config, game_controller, plugin_manager):
        self.config = config
        self.game_controller = game_controller
        self.plugin_manager = plugin_manager
        self.connector = ServerConnector(config)
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
                    logger.warning("Game not running. Waiting...")
                elif state in ("main_menu", "multiplayer", "favorites", "server_list"):
                    # Запускаємо повний цикл підключення
                    success = self.connector.connect()
                    if success:
                        logger.info("Connected! Monitoring game state...")
                        # Чекаємо, поки гра закінчиться (стан стане не in_game)
                        while self.running and self.game_controller.get_game_state() == "in_game":
                            time.sleep(10)
                elif state in ("queue",):
                    # Просто чекаємо, конектор сам обробить чергу
                    pass
                time.sleep(5)
            except Exception as e:
                logger.error(f"Automation error: {e}")
                time.sleep(10)