import threading
import time
import telebot
from loguru import logger
from core.license_manager import LicenseManager

class TelegramBot:
    def __init__(self, config, license_manager, game_controller):
        self.config = config
        self.license_manager = license_manager
        self.game_controller = game_controller
        self.token = config.get("telegram_token", "")
        self.bot = None
        self.thread = None
        self.running = False

    def start(self):
        if not self.token:
            logger.warning("Telegram token not set, bot not started")
            return
        self.bot = telebot.TeleBot(self.token)
        self._register_handlers()
        self.running = True
        self.thread = threading.Thread(target=self._run_polling, daemon=True)
        self.thread.start()
        logger.info("Telegram bot started")

    def stop(self):
        self.running = False
        if self.bot:
            self.bot.stop_polling()
        logger.info("Telegram bot stopped")

    def _run_polling(self):
        while self.running:
            try:
                self.bot.polling(none_stop=True, interval=1)
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                time.sleep(5)

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self.bot.reply_to(message, "Arma Reforger Bot: /status, /screenshot, /run_game")

        @self.bot.message_handler(commands=['status'])
        def status(message):
            state = self.game_controller.get_game_state()
            self.bot.reply_to(message, f"Game state: {state}")

        @self.bot.message_handler(commands=['screenshot'])
        def screenshot(message):
            # Робить скріншот та відправляє
            import io
            from PIL import ImageGrab
            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            self.bot.send_photo(message.chat.id, buf)

        @self.bot.message_handler(commands=['run_game'])
        def run_game(message):
            # Запускає гру (заглушка)
            self.bot.reply_to(message, "Game launch triggered")

        @self.bot.message_handler(commands=['genlicense'])
        def genlicense(message):
            if message.chat.id != 390469052:
                self.bot.reply_to(message, "Access denied")
                return
            # Очікує формат /genlicense USER_ID DAYS
            args = message.text.split()
            if len(args) != 3:
                self.bot.reply_to(message, "Usage: /genlicense USER_ID DAYS")
                return
            user_id, days = args[1], args[2]
            try:
                days_int = int(days)
            except:
                self.bot.reply_to(message, "Days must be integer")
                return
            # Генеруємо простий ключ на основі user_id
            license_key = f"ARMA-{user_id}-{int(time.time())}"
            # Зберігаємо (у реальному житті потрібна БД)
            # Тут просто відправляємо ключ користувачу
            self.bot.send_message(user_id, f"Your license key: {license_key} (valid for {days} days)")
            self.bot.reply_to(message, f"License generated for user {user_id}")