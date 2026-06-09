from core.base_plugin import BasePlugin
from loguru import logger
from PySide6.QtCore import QObject, Signal, QTimer
import threading
import time

class QueueProgressBarPlugin(BasePlugin):
    def get_name(self):
        return "Прогрес-бар черги"

    def get_description(self):
        return "Оновлює прогрес-бари черги сервера та фракції на головній вкладці"

    def on_enable(self):
        self.running = True
        self.thread = threading.Thread(target=self._update_bars, daemon=True)
        self.thread.start()
        logger.info("Queue progress bar enabled")

    def on_disable(self):
        self.running = False
        logger.info("Queue progress bar disabled")

    def _update_bars(self):
        while self.running:
            # У реальному коді потрібен доступ до головного вікна через сигнали
            # Тут спрощено
            time.sleep(2)