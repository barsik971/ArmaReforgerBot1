import sys
import os
import threading
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from loguru import logger
from core.config_manager import ConfigManager
from core.license_manager import LicenseManager
from core.telegram_bot import TelegramBot
from core.plugin_manager import PluginManager
from core.game_controller import GameController
from core.automation import Automation
from core.web_server import WebServer
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

    # PluginManager (поки без головного вікна)
    plugin_manager = PluginManager(config, game_controller, license_manager, main_window=None)

    # Automation
    automation = Automation(config, game_controller, plugin_manager)

    # Telegram бот
    telegram_bot = TelegramBot(config, license_manager, game_controller, automation, plugin_manager)
    if config.get("telegram_enabled", True):
        telegram_bot.start()

    # Запускаємо Web Server у фоновому потоці
    web_server = WebServer(config, game_controller, automation, plugin_manager, license_manager, telegram_bot)
    web_thread = threading.Thread(target=web_server.run, daemon=True)
    web_thread.start()
    logger.info("Web server started on http://localhost:5000")

    # GUI
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow(config, license_manager, plugin_manager, game_controller, telegram_bot)

    # Передаємо вікно в plugin_manager
    plugin_manager.main_window = window
    plugin_manager.load_plugins()

    if hasattr(window, 'add_log_handler'):
        window.add_log_handler()

    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()