import threading
import time
from loguru import logger

class Automation:
    def __init__(self, config, game_controller, plugin_manager):
        self.config = config
        self.game_controller = game_controller
        self.plugin_manager = plugin_manager
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
                if state == "server_list":
                    self.game_controller.click_filter_positions()
                    server = self.config.get("server_name")
                    self.game_controller.connect_to_server(server)
                elif state == "faction_queue":
                    threshold = self.config.get("queue_threshold")
                    if self.game_controller.is_queue_below_threshold(threshold):
                        # тут має бути клік на "join" або подібне
                        pass
            except Exception as e:
                logger.error(f"Automation error: {e}")
            time.sleep(5)