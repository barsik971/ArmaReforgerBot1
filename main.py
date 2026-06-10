import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
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

    # 1. Конфіг
    config_path = Path("config.json")
    config = ConfigManager(config_path)

    # 2. Ліцензія
    license_manager = LicenseManager(config)

    # 3. Контролер гри
    game_controller = GameController(config)

    # 4. Плагін-менеджер (без головного вікна)
    plugin_manager = PluginManager(config, game_controller, license_manager, main_window=None)

    # 5. Автоматизація
    automation = Automation(config, game_controller, plugin_manager)

    # 6. Telegram-бот
    telegram_bot = TelegramBot(config, license_manager, game_controller, automation, plugin_manager)
    if config.get("telegram_enabled", True):
        telegram_bot.start()

    # 7. GUI
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow(config, license_manager, plugin_manager, game_controller, telegram_bot)

    # 8. Передаємо вікно плагін-менеджеру та завантажуємо плагіни
    plugin_manager.main_window = window
    plugin_manager.load_plugins()

    # 9. Підключаємо логування в GUI
    if hasattr(window, 'add_log_handler'):
        window.add_log_handler()

    window.show()

    # 10. Запускаємо головний цикл
    sys.exit(app.exec())

if __name__ == "__main__":
    main()