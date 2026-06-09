from core.base_plugin import BasePlugin
from loguru import logger
import shutil
import os

class GraphicsConfigBackupPlugin(BasePlugin):
    def get_name(self):
        return "Резервне копіювання конфігурації графіки"

    def get_description(self):
        return "Зберігає та відновлює .cfg файли гри"

    def on_enable(self):
        self.backup()
        logger.info("Graphics config backed up")

    def on_disable(self):
        pass

    def backup(self):
        config_dir = os.path.expandvars(r"%USERPROFILE%\Documents\My Games\ArmaReforger")
        backup_dir = "graphics_backup"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        for file in os.listdir(config_dir):
            if file.endswith('.cfg'):
                shutil.copy2(os.path.join(config_dir, file), backup_dir)
        logger.info(f"Configs backed up to {backup_dir}")

    def restore(self):
        backup_dir = "graphics_backup"
        config_dir = os.path.expandvars(r"%USERPROFILE%\Documents\My Games\ArmaReforger")
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                shutil.copy2(os.path.join(backup_dir, file), config_dir)
            logger.info("Graphics config restored")