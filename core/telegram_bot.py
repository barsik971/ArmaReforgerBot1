import threading
import time
import telebot
from telebot import types
import hmac
import hashlib
import io
from loguru import logger
from PIL import ImageGrab

SIGNING_KEY = b"replace_with_strong_random_key_1234567890"

class TelegramBot:
    def __init__(self, config, license_manager, game_controller, automation=None, plugin_manager=None):
        self.config = config
        self.license_manager = license_manager
        self.game_controller = game_controller
        self.automation = automation
        self.plugin_manager = plugin_manager
        self.token = config.get("telegram_token", "")
        self.admin_chat_id = config.get("admin_chat_id", 390469052)
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

    # ---------- Головне меню ----------
    def _main_keyboard(self):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn_status = types.KeyboardButton("📊 Статус гри")
        btn_queue = types.KeyboardButton("🕒 Черга")
        btn_screenshot = types.KeyboardButton("📸 Скріншот")
        btn_automation = types.KeyboardButton("🤖 Керування авто")
        btn_plugins = types.KeyboardButton("🔌 Плагіни")
        btn_app = types.KeyboardButton("📱 Відкрити Web App")
        btn_monitor = types.KeyboardButton("📡 Моніторинг серверів")  # нова кнопка
        keyboard.add(btn_status, btn_queue, btn_screenshot, btn_automation,
                     btn_plugins, btn_app, btn_monitor)
        return keyboard

    # ---------- Реєстрація обробників ----------
    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.bot.send_message(
                message.chat.id,
                "🎮 *Arma Reforger Bot* – ваш віддалений помічник.\nОберіть дію:",
                parse_mode="Markdown",
                reply_markup=self._main_keyboard()
            )

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            text = message.text
            if text == "📊 Статус гри":
                self._send_status(message.chat.id)
            elif text == "🕒 Черга":
                self._send_queue(message.chat.id)
            elif text == "📸 Скріншот":
                self._send_screenshot(message.chat.id)
            elif text == "🤖 Керування авто":
                self._send_automation_menu(message.chat.id)
            elif text == "🔌 Плагіни":
                self._send_plugins_menu(message.chat.id)
            elif text == "📱 Відкрити Web App":
                self._send_webapp(message.chat.id)
            elif text == "📡 Моніторинг серверів":       # обробка нової кнопки
                self._send_monitor_menu(message.chat.id)
            elif text == "⬅️ Назад":
                self.bot.send_message(message.chat.id, "Головне меню",
                                      reply_markup=self._main_keyboard())
            else:
                if message.text.startswith('/genlicense') and message.chat.id == self.admin_chat_id:
                    self._genlicense_command(message)
                else:
                    self.bot.send_message(message.chat.id, "Використовуйте кнопки меню.",
                                          reply_markup=self._main_keyboard())

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            if call.data.startswith("auto_"):
                self._handle_automation_callback(call)
            elif call.data.startswith("plug_"):
                self._handle_plugin_callback(call)
            elif call.data.startswith("monitor_"):      # нові колбеки для моніторингу
                self._handle_monitor_callback(call)

    # ---------- Існуючі методи (скорочено, вони є у вас) ----------
    def _send_status(self, chat_id):
        state = self.game_controller.get_game_state()
        self.bot.send_message(chat_id, f"📊 Стан гри: *{state}*", parse_mode="Markdown")

    def _send_queue(self, chat_id):
        pos = self.game_controller.get_queue_position()
        self.bot.send_message(chat_id, f"🕒 Поточна черга: *{pos}*", parse_mode="Markdown")

    def _send_screenshot(self, chat_id):
        try:
            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            self.bot.send_photo(chat_id, buf, caption="📸 Поточний екран")
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ Помилка скріншота: {e}")

    def _send_automation_menu(self, chat_id):
        markup = types.InlineKeyboardMarkup(row_width=2)
        if self.automation and self.automation.running:
            status = "🟢 Автоматизація активна"
            btn_toggle = types.InlineKeyboardButton("⏹ Зупинити", callback_data="auto_stop")
        else:
            status = "🔴 Автоматизація вимкнена"
            btn_toggle = types.InlineKeyboardButton("▶️ Запустити", callback_data="auto_start")
        btn_connect = types.InlineKeyboardButton("🔌 Підключитись зараз", callback_data="auto_connect")
        markup.add(btn_toggle, btn_connect)
        self.bot.send_message(chat_id, f"🤖 *Керування автоматизацією*\n{status}",
                              parse_mode="Markdown", reply_markup=markup)

    def _handle_automation_callback(self, call):
        chat_id = call.message.chat.id
        if call.data == "auto_start":
            if self.automation:
                self.automation.start()
                self.bot.answer_callback_query(call.id, "Автоматизацію запущено")
                self._send_automation_menu(chat_id)
        elif call.data == "auto_stop":
            if self.automation:
                self.automation.stop()
                self.bot.answer_callback_query(call.id, "Автоматизацію зупинено")
                self._send_automation_menu(chat_id)
        elif call.data == "auto_connect":
            self.bot.answer_callback_query(call.id, "Запускаю підключення...")
            threading.Thread(target=self._run_manual_connect, args=(chat_id,), daemon=True).start()

    def _run_manual_connect(self, chat_id):
        if self.automation and hasattr(self.automation, 'connector'):
            self.bot.send_message(chat_id, "⏳ Підключення розпочато...")
            result = self.automation.connector.connect()
            if result:
                self.bot.send_message(chat_id, "✅ Успішно підключено до сервера!")
            else:
                self.bot.send_message(chat_id, "❌ Не вдалося підключитись.")
        else:
            self.bot.send_message(chat_id, "❌ Automation не ініціалізовано.")

    # ---------- Плагіни ----------
    def _send_plugins_menu(self, chat_id):
        if not self.plugin_manager:
            self.bot.send_message(chat_id, "Плагіни недоступні.")
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        plugins = self.plugin_manager.get_plugin_list()
        for p in plugins:
            status = "✅" if p.is_enabled() else "❌"
            btn_text = f"{status} {p.get_name()}"
            callback = f"plug_toggle_{p.get_name()}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback))
        self.bot.send_message(chat_id, "🔌 *Керування плагінами*", parse_mode="Markdown", reply_markup=markup)

    def _handle_plugin_callback(self, call):
        chat_id = call.message.chat.id
        if not self.plugin_manager:
            return
        if call.data.startswith("plug_toggle_"):
            plugin_name = call.data.replace("plug_toggle_", "")
            if plugin_name in self.plugin_manager.plugins:
                if self.plugin_manager.plugins[plugin_name].is_enabled():
                    self.plugin_manager.disable_plugin(plugin_name)
                    self.bot.answer_callback_query(call.id, f"Плагін '{plugin_name}' вимкнено")
                else:
                    if not self.license_manager.is_pro():
                        self.bot.answer_callback_query(call.id, "Потрібна Pro-версія", show_alert=True)
                        return
                    success = self.plugin_manager.enable_plugin(plugin_name)
                    if success:
                        self.bot.answer_callback_query(call.id, f"Плагін '{plugin_name}' увімкнено")
                    else:
                        self.bot.answer_callback_query(call.id, "Помилка активації")
                self._send_plugins_menu(chat_id)

    # ---------- НОВЕ: Моніторинг серверів ----------
    def _send_monitor_menu(self, chat_id):
        if not self.plugin_manager:
            self.bot.send_message(chat_id, "Плагіни недоступні.")
            return
        plugin = self.plugin_manager.plugins.get("Мультисерверний моніторинг")
        if not plugin:
            self.bot.send_message(chat_id, "Плагін моніторингу не встановлено.")
            return
        status = "🟢 Активний" if plugin.is_enabled() else "🔴 Неактивний"
        markup = types.InlineKeyboardMarkup(row_width=1)
        if plugin.is_enabled():
            btn = types.InlineKeyboardButton("⏹ Вимкнути", callback_data="monitor_disable")
        else:
            btn = types.InlineKeyboardButton("▶️ Увімкнути", callback_data="monitor_enable")
        markup.add(btn)
        self.bot.send_message(chat_id, f"📡 Моніторинг серверів\nСтатус: {status}",
                              parse_mode="Markdown", reply_markup=markup)

    def _handle_monitor_callback(self, call):
        chat_id = call.message.chat.id
        if not self.plugin_manager:
            return
        if call.data == "monitor_enable":
            if not self.license_manager.is_pro():
                self.bot.answer_callback_query(call.id, "Потрібна Pro-версія", show_alert=True)
                return
            success = self.plugin_manager.enable_plugin("Мультисерверний моніторинг")
            if success:
                self.bot.answer_callback_query(call.id, "Моніторинг увімкнено")
            else:
                self.bot.answer_callback_query(call.id, "Помилка при ввімкненні")
            self._send_monitor_menu(chat_id)
        elif call.data == "monitor_disable":
            self.plugin_manager.disable_plugin("Мультисерверний моніторинг")
            self.bot.answer_callback_query(call.id, "Моніторинг вимкнено")
            self._send_monitor_menu(chat_id)

    # ---------- Web App (заглушка) ----------
    def _send_webapp(self, chat_id):
        webapp_url = "https://your-domain.com/app"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Відкрити веб-інтерфейс", url=webapp_url)
        markup.add(btn)
        self.bot.send_message(chat_id, "📱 Натисніть, щоб відкрити панель керування:", reply_markup=markup)

    # ---------- Адмін-команда /genlicense ----------
    def _genlicense_command(self, message):
        if message.chat.id != self.admin_chat_id:
            self.bot.reply_to(message, "Доступ заборонено")
            return
        args = message.text.split()
        if len(args) != 3:
            self.bot.reply_to(message, "Формат: /genlicense USER_ID DAYS")
            return
        user_id, days = args[1], args[2]
        try:
            days_int = int(days)
        except:
            self.bot.reply_to(message, "Кількість днів має бути числом")
            return
        if days_int == 0:
            expiry_str = "never"
        else:
            expiry_ts = int(time.time()) + days_int * 86400
            expiry_str = str(expiry_ts)
        data = f"{user_id}:{expiry_str}".encode()
        signature = hmac.new(SIGNING_KEY, data, hashlib.sha256).hexdigest()
        license_key = f"{user_id}:{expiry_str}:{signature}"
        self.bot.send_message(user_id, f"🔑 Ваш ключ активації:\n`{license_key}`", parse_mode="Markdown")
        self.bot.reply_to(message, f"✅ Ключ для {user_id} створено")

    # ---------- Сповіщення адміністратору ----------
    def notify_admin(self, text):
        try:
            self.bot.send_message(self.admin_chat_id, text, parse_mode="Markdown")
        except:
            pass