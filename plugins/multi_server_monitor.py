import threading
import time
from pathlib import Path
from core.base_plugin import BasePlugin
from loguru import logger
from core.server_scanner import ServerScanner

class MultiServerMonitorPlugin(BasePlugin):
    def get_name(self):
        return "Мультисерверний моніторинг"

    def get_description(self):
        return "Відстежує кілька серверів та сповіщає в Telegram, коли з'являється місце"

    def on_enable(self):
        self.running = True
        self.scanner = ServerScanner(self.config)
        self.servers = self.config.get("monitored_servers", [])
        if not self.servers:
            logger.warning("Список серверів для моніторингу порожній")
        self.interval = self.config.get("monitor_interval", 30)  # секунд
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Моніторинг серверів запущено")

    def on_disable(self):
        self.running = False
        logger.info("Моніторинг серверів зупинено")

    def _monitor_loop(self):
        while self.running:
            try:
                for server in self.servers:
                    name = server.get("name")
                    if not name:
                        continue
                    max_queue = server.get("max_queue", 24)
                    max_players = server.get("max_players", 128)

                    players, current_max, queue = self.scanner.find_server_info(name, max_scroll=5)
                    if players is not None:
                        logger.debug(f"{name}: {players}/{current_max}, черга {queue}")
                        if players < current_max and queue <= max_queue:
                            self._notify_admin(
                                f"🟢 З'явилося місце на сервері **{name}**\n"
                                f"Гравців: {players}/{current_max}\n"
                                f"Черга: {queue}"
                            )
                            # Щоб не спамити, можна прибрати сервер зі списку або поставити прапорець,
                            # але поки що просто повідомляємо один раз і продовжуємо моніторити.
            except Exception as e:
                logger.error(f"Помилка моніторингу: {e}")
            time.sleep(self.interval)

    def _notify_admin(self, message):
        # Отримуємо доступ до Telegram-бота через головне вікно
        # Плагін не має прямого доступу до MainWindow, але ми можемо передати його через set_main_window
        # Або використати статичний/глобальний об'єкт. Зробимо через main_window, який ми вже передаємо.
        if hasattr(self, 'main_window') and self.main_window:
            telegram_bot = getattr(self.main_window, 'telegram_bot', None)
            if telegram_bot:
                telegram_bot.notify_admin(message)
            else:
                logger.warning("TelegramBot не знайдено")
        else:
            logger.warning("MainWindow не приєднано до плагіна")