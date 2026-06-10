from core.base_plugin import BasePlugin
from loguru import logger
from PySide6.QtCore import QTimer

class QueueProgressBarPlugin(BasePlugin):
    def __init__(self, config, game_controller):
        super().__init__(config, game_controller)
        self.main_window = None
        self.timer = None

    def set_main_window(self, mw):
        self.main_window = mw

    def get_name(self):
        return "Прогрес-бар черги"

    def get_description(self):
        return "Оновлює прогрес-бари черги сервера та фракції на головній вкладці"

    def on_enable(self):
        if self.main_window:
            # Таймер вже є в MainWindow, тому просто логуємо
            logger.info("Queue progress bar enabled (MainWindow timer active)")
        else:
            logger.warning("MainWindow not set for QueueProgressBarPlugin")

    def on_disable(self):
        logger.info("Queue progress bar disabled")