import sys
import os
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from loguru import logger
from core.config_manager import ConfigManager
from core.license_manager import LicenseManager
from core.telegram_bot import TelegramBot
from core.plugin_manager import PluginManager
from core.game_controller import GameController
from gui.main_window import MainWindow

def setup_logger():
    logger.remove()
    logger.add("bot.log", rotation="1 MB", level="DEBUG", format="{time} {level} {message}")
    logger.add(sys.stdout, level="INFO", format="<green>{time}</green> <level>{message}</level>")

def main():
    setup_logger()
    logger.info("Starting Arma Reforger Auto Bot")

    # Ініціалізація конфігурації
    config_path = Path("config.json")
    config = ConfigManager(config_path)

    # Ліцензування
    license_manager = LicenseManager(config)

    # Ігровий контролер
    game_controller = GameController(config)

    # Менеджер плагінів
    plugin_manager = PluginManager(config, game_controller)
    plugin_manager.load_plugins()

    # Telegram бот (запускається завжди)
    telegram_bot = TelegramBot(config, license_manager, game_controller)
    if config.get("telegram_enabled", True):
        telegram_bot.start()

    # Головне вікно
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow(config, license_manager, plugin_manager, game_controller, telegram_bot)
    window.show()

    # Запуск основної автоматизації (автопідключення тощо)
    from core.automation import Automation
    automation = Automation(config, game_controller, plugin_manager)
    automation.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()