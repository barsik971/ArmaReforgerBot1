from core.base_plugin import BasePlugin
from loguru import logger
import threading
import time
import psutil
import GPUtil
import winsound

class TemperatureMonitorPlugin(BasePlugin):
    def get_name(self):
        return "Моніторинг температури"

    def get_description(self):
        return "Відстежує температуру CPU/GPU, сповіщає через звук та Telegram"

    def on_enable(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        logger.info("Temperature monitor enabled")

    def on_disable(self):
        self.running = False
        logger.info("Temperature monitor disabled")

    def _monitor(self):
        while self.running:
            try:
                cpu_temp = None
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if 'coretemp' in temps:
                        cpu_temp = temps['coretemp'][0].current
                gpus = GPUtil.getGPUs()
                gpu_temp = gpus[0].temperature if gpus else None

                if cpu_temp and cpu_temp > 85:
                    self.alert(f"CPU temperature critical: {cpu_temp}°C")
                if gpu_temp and gpu_temp > 85:
                    self.alert(f"GPU temperature critical: {gpu_temp}°C")
            except Exception as e:
                logger.error(f"Temperature monitor error: {e}")
            time.sleep(10)

    def alert(self, message):
        winsound.Beep(1000, 500)
        logger.warning(message)
        # Можна відправити в Telegram через бота, якщо доступний
        # Тут реалізація залежить від доступу до TelegramBot