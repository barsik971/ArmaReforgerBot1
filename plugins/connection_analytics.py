from core.base_plugin import BasePlugin
from loguru import logger
import json
import time
from datetime import datetime
from pathlib import Path

class ConnectionAnalyticsPlugin(BasePlugin):
    def get_name(self):
        return "Аналітика підключень"

    def get_description(self):
        return "Записує успішні/невдалі спроби, чергу, час очікування"

    def on_enable(self):
        self.file = Path("connection_log.json")
        self.running = True
        # Тут потрібно інтегруватися з automation для отримання даних
        logger.info("Connection analytics enabled")

    def on_disable(self):
        self.running = False
        logger.info("Connection analytics disabled")

    def log_attempt(self, success, queue_size, wait_time):
        record = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "queue": queue_size,
            "wait_time": wait_time
        }
        try:
            if self.file.exists():
                with open(self.file, 'r') as f:
                    data = json.load(f)
            else:
                data = []
            data.append(record)
            with open(self.file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Analytics logging failed: {e}")