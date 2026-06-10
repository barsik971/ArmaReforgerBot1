import sys, os
from pathlib import Path
from PySide6.QtWidgets import QApplication
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

    # Telegram бот
    telegram_bot = TelegramBot(config, license_manager, game_controller)
    if config.get("telegram_enabled", True):
        telegram_bot.start()

    # Створюємо вікно (плагін менеджер створимо після, бо потрібне посилання на вікно)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Тимчасово створюємо plugin_manager без main_window, потім оновимо
    plugin_manager = PluginManager(config, game_controller, license_manager, main_window=None)

    window = MainWindow(config, license_manager, plugin_manager, game_controller, telegram_bot)

    # Оновлюємо plugin_manager, передаючи вікно
    plugin_manager.main_window = window
    plugin_manager.load_plugins()   # тепер плагіни отримають доступ до вікна

    window.add_log_handler()  # підключаємо логування в GUI
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()