from core.base_plugin import BasePlugin
from loguru import logger
import shutil
import os

class ShaderCacheCleanerPlugin(BasePlugin):
    def get_name(self):
        return "Очищення кешу шейдерів"

    def get_description(self):
        return "Видаляє папку Cache Arma Reforger"

    def on_enable(self):
        self.clean()
        logger.info("Shader cache cleaned")

    def on_disable(self):
        pass

    def clean(self):
        # Шлях до кешу (приклад)
        cache_path = os.path.expandvars(r"%LOCALAPPDATA%\ArmaReforger\Cache")
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
            logger.info(f"Deleted: {cache_path}")