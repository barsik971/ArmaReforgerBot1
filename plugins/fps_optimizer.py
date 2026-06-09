from core.base_plugin import BasePlugin
from loguru import logger
import psutil
import os

class FPSOptimizerPlugin(BasePlugin):
    def get_name(self):
        return "Оптимізація FPS"

    def get_description(self):
        return "Підвищує пріоритет процесу ArmaReforger.exe та закриває фонові програми"

    def on_enable(self):
        self.optimize()
        logger.info("FPS optimization applied")

    def on_disable(self):
        logger.info("FPS optimization cannot be fully reverted")

    def optimize(self):
        # Підвищення пріоритету
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and 'ArmaReforger' in proc.info['name']:
                try:
                    p = psutil.Process(proc.info['pid'])
                    p.nice(psutil.HIGH_PRIORITY_CLASS)
                    logger.info(f"Priority set for {proc.info['name']}")
                except Exception as e:
                    logger.error(f"Failed to set priority: {e}")

        # Закриття деяких фонових процесів (приклад)
        unwanted = ['chrome.exe', 'discord.exe']
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and proc.info['name'].lower() in unwanted:
                try:
                    proc.terminate()
                    logger.info(f"Terminated {proc.info['name']}")
                except:
                    pass