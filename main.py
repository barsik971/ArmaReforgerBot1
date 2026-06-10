import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
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
    if sys.stdout is not None:
        logger.add(sys.stdout, level="INFO", format="<green>{time}</green> <level>{message}</level>")

def main():
    setup_logger()
    logger.info("Starting Arma Reforger Auto Bot")

    config_path = Path("config.json")
    config = ConfigManager(config_path)

    license_manager = LicenseManager(config)
    game_controller = GameController(config)

    # Telegram бот (запускається завжди, якщо є токен)
    telegram_bot = TelegramBot(config, license_manager, game_controller)
    if config.get("telegram_enabled", True):
        telegram_bot.start()

    # Створюємо GUI
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # PluginManager створюємо без main_window, передамо пізніше
    plugin_manager = PluginManager(config, game_controller, license_manager, main_window=None)

    window = MainWindow(config, license_manager, plugin_manager, game_controller, telegram_bot)

    # Тепер оновлюємо plugin_manager, передаючи посилання на вікно
    plugin_manager.main_window = window
    # Завантажуємо плагіни (тепер вони отримають доступ до вікна)
    plugin_manager.load_plugins()

    # Підключаємо логування в GUI (якщо реалізовано)
    if hasattr(window, 'add_log_handler'):
        window.add_log_handler()

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()