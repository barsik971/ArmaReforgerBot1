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
from core.automation import Automation
from gui.main_window import MainWindow

def setup_logger():
    logger.remove()
    logger.add("bot.log", rotation="1 MB", level="DEBUG", format="{time} {level} {message}")
    if sys.stdout is not None:
        logger.add(sys.stdout, level="INFO", format="<green>{time}</green> <level>{message}</level>")

def main():
    setup_logger()
    logger.info("Starting Arma Reforger Auto Bot")

    # 1. СТВОРЮЄМО КОНФІГ ПЕРШИМ
    config_path = Path("config.json")
    config = ConfigManager(config_path)

    # 2. Ліцензія
    license_manager = LicenseManager(config)

    # 3. Ігровий контролер
    game_controller = GameController(config)

    # 4. PluginManager (поки без головного вікна)
    plugin_manager = PluginManager(config, game_controller, license_manager, main_window=None)

    # 5. Automation (використовує AdaptiveConnector)
    automation = Automation(config, game_controller, plugin_manager)

    # 6. Telegram-бот (тепер config вже існує)
    telegram_bot = TelegramBot(config, license_manager, game_controller, automation, plugin_manager)
    if config.get("telegram_enabled", True):
        telegram_bot.start()

    # 7. Створюємо GUI
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow(config, license_manager, plugin_manager, game_controller, telegram_bot)

    # 8. Передаємо головне вікно в plugin_manager
    plugin_manager.main_window = window

    # 9. Завантажуємо плагіни (тепер вони можуть отримати доступ до вікна)
    plugin_manager.load_plugins()

    # 10. Підключаємо логування в GUI (якщо метод існує)
    if hasattr(window, 'add_log_handler'):
        window.add_log_handler()

    # 11. Показуємо вікно
    window.show()

    # 12. Запускаємо головний цикл
    sys.exit(app.exec())

if __name__ == "__main__":
    main()