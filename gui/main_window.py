import os, math, threading
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QTextEdit, QSpinBox, QSystemTrayIcon, QMenu, QApplication, QProgressBar, QStyle
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QAction, QIcon, QPainter, QLinearGradient, QColor, QFont
from loguru import logger
from core.license_manager import LicenseManager
from core.plugin_manager import PluginManager
from core.game_controller import GameController
from core.telegram_bot import TelegramBot
from core.automation import Automation
from gui.macro_dialog import MacroDialog
import winsound


# ---- Сигнал для безпечного оновлення GUI з інших потоків ----
class LogSignal(QObject):
    new_message = Signal(str)

class AnimatedBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(40)
        self.angle = 0
        self.color1 = QColor(255, 80, 0)
        self.color2 = QColor(200, 0, 200)
        self.color3 = QColor(0, 200, 255)

    def set_theme_colors(self, theme_name):
        if theme_name == "lava":
            self.color1 = QColor(255, 80, 0)
            self.color2 = QColor(200, 0, 200)
            self.color3 = QColor(0, 200, 255)
        elif theme_name == "neon":
            self.color1 = QColor(0, 255, 200)
            self.color2 = QColor(255, 0, 255)
            self.color3 = QColor(0, 200, 255)
        elif theme_name == "cyberpunk":
            self.color1 = QColor(255, 0, 150)
            self.color2 = QColor(102, 0, 204)
            self.color3 = QColor(0, 255, 0)
        elif theme_name == "classic":
            self.color1 = QColor(240, 240, 240)
            self.color2 = QColor(200, 200, 200)
            self.color3 = QColor(150, 150, 150)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        self.angle = (self.angle + 2) % 360
        rad = math.radians(self.angle)
        w, h = rect.width(), rect.height()
        cx, cy = w/2, h/2
        r = min(w, h) * 0.7
        x1 = cx + r * math.cos(rad)
        y1 = cy + r * math.sin(rad)
        x2 = cx - r * math.cos(rad)
        y2 = cy - r * math.sin(rad)
        gradient = QLinearGradient(x1, y1, x2, y2)
        gradient.setColorAt(0.0, self.color1)
        gradient.setColorAt(0.5, self.color2)
        gradient.setColorAt(1.0, self.color3)
        painter.setBrush(gradient)
        painter.drawRect(rect)


class MainWindow(QMainWindow):
    
    def _manual_connect(self):
        if not self.license_manager.is_pro():
            self._append_log("Потрібна Pro-версія для ручного підключення")
            return
        import threading
        threading.Thread(target=self._connect_thread, daemon=True).start()

    def _connect_thread(self):
        from core.server_connector import ServerConnector
        self._append_log("Запуск підключення вручну...")
        connector = ServerConnector(self.config)
        result = connector.connect()
        if result:
            self._append_log("Підключення успішне!")
            self.play_sound(1000, 200)
        else:
            self._append_log("Не вдалося підключитись")

    def __init__(self, config, license_manager, plugin_manager, game_controller, telegram_bot):
        super().__init__()
        self.config = config
        self.license_manager = license_manager
        self.plugin_manager = plugin_manager
        self.game_controller = game_controller
        self.telegram_bot = telegram_bot
        self.automation = None   # буде створено пізніше

        self.setWindowTitle("Arma Reforger Auto Bot")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        # Фон
        self.background = AnimatedBackground(self)
        self.setCentralWidget(self.background)

        main_widget = QWidget(self.background)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Заголовок
        self.title_label = QLabel("Arma Reforger Auto Bot")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 20, QFont.Bold))
        main_layout.addWidget(self.title_label)

        # Вкладки
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Створюємо вкладки
        self.dashboard_tab = QWidget()
        self.tabs.addTab(self.dashboard_tab, "Головна")
        self.init_dashboard_tab()


        self.plugins_tab = QWidget()
        self.tabs.addTab(self.plugins_tab, "Плагіни")
        self.init_plugins_tab()

        self.activation_tab = QWidget()
        self.tabs.addTab(self.activation_tab, "Активація")
        self.init_activation_tab()

        self.macros_tab = QWidget()
        self.tabs.addTab(self.macros_tab, "Макроси")
        self.init_macros_tab()

        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Налаштування")
        self.init_settings_tab()

        # Лог (віджет для виводу)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        main_layout.addWidget(QLabel("Лог:"))
        main_layout.addWidget(self.log_output)

        # Системний трей
        self.init_tray()

        # Звук
        self.sound_enabled = config.get("sound_enabled", True)

        # Тема
        self.current_theme = config.get("theme", "lava")
        self.apply_theme(self.current_theme)

        # Підключаємо логування до GUI через сигнал
        self.log_signal = LogSignal()
        self.log_signal.new_message.connect(self._append_log)

        # Автоматизація (створюється тут, бо потрібен plugin_manager)
        self.automation = Automation(config, game_controller, plugin_manager)

        # Таймер для оновлення прогрес-барів (черга сервера/фракції)
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self._update_queue_bars)
        self.queue_timer.start(3000)  # кожні 3 секунди

    # ---- Dashboard ----
    def init_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        self.state_label = QLabel("Стан гри: невідомо")
        self.queue_label = QLabel("Черга сервера: N/A")
        layout.addWidget(self.state_label)
        layout.addWidget(self.queue_label)

        self.server_queue_bar = QProgressBar()
        self.server_queue_bar.setMaximum(100)
        layout.addWidget(QLabel("Прогрес черги сервера:"))
        layout.addWidget(self.server_queue_bar)

        self.faction_queue_bar = QProgressBar()
        layout.addWidget(QLabel("Черга фракції:"))
        layout.addWidget(self.faction_queue_bar)

        btn_start = QPushButton("▶ Запустити авто")
        btn_stop = QPushButton("⏹ Зупинити авто")
        btn_start.clicked.connect(self._start_automation)
        btn_stop.clicked.connect(self._stop_automation)
        layout.addWidget(btn_start)
        layout.addWidget(btn_stop)
        # Ось тут додайте:
        btn_connect = QPushButton("🔌 Підключитись зараз")
        btn_connect.clicked.connect(self._manual_connect)
        layout.addWidget(btn_connect)

    def _start_automation(self):
        if self.automation:
            self.automation.start()
            self._append_log("Автоматизацію запущено")

    def _stop_automation(self):
        if self.automation:
            self.automation.stop()
            self._append_log("Автоматизацію зупинено")

    def _update_queue_bars(self):
        # Оновлюємо інформацію про чергу з game_controller
        try:
            queue_pos = self.game_controller.get_queue_position()
            self.queue_label.setText(f"Черга сервера: {queue_pos}")
            # Припустимо, що черга від 0 до 100 (для прикладу)
            self.server_queue_bar.setValue(min(queue_pos, 100))
            # Фракційна черга – заглушка
            self.faction_queue_bar.setValue(0)
            state = self.game_controller.get_game_state()
            self.state_label.setText(f"Стан гри: {state}")
        except Exception as e:
            logger.error(f"Помилка оновлення черги: {e}")

    # ---- Плагіни ----
    def init_plugins_tab(self):
        layout = QVBoxLayout(self.plugins_tab)
        self.plugin_checkboxes = {}
        for plugin in self.plugin_manager.get_plugin_list():
            cb = QCheckBox(plugin.get_name())
            cb.setChecked(plugin.is_enabled())
            cb.stateChanged.connect(lambda state, p=plugin: self.toggle_plugin(p, state))
            layout.addWidget(cb)
            self.plugin_checkboxes[plugin.get_name()] = cb
            desc = QLabel(plugin.get_description())
            layout.addWidget(desc)

    def toggle_plugin(self, plugin, state):
        # Перевірка Pro для плагінів (окрім базових, якщо треба)
        if state and not self.license_manager.is_pro():
            self._append_log("Потрібна Pro-версія для активації плагіна")
            # Знімаємо галочку назад
            cb = self.plugin_checkboxes.get(plugin.get_name())
            if cb:
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
            return
        if state:
            success = self.plugin_manager.enable_plugin(plugin.get_name())
            if success:
                self._append_log(f"Плагін '{plugin.get_name()}' увімкнено")
        else:
            success = self.plugin_manager.disable_plugin(plugin.get_name())
            if success:
                self._append_log(f"Плагін '{plugin.get_name()}' вимкнено")

    # ---- Активація ----
    def init_activation_tab(self):
        layout = QVBoxLayout(self.activation_tab)
        layout.addWidget(QLabel("Введіть секретне слово або ліцензійний ключ:"))
        self.activation_input = QLineEdit()
        layout.addWidget(self.activation_input)
        btn_activate = QPushButton("Активувати")
        btn_activate.clicked.connect(self.activate)
        layout.addWidget(btn_activate)
        self.activation_status = QLabel("")
        layout.addWidget(self.activation_status)

    def activate(self):
        word = self.activation_input.text().strip()
        if self.license_manager.activate_secret(word):
            self.activation_status.setText("Pro активовано (секретне слово)")
            self._append_log("Pro активовано через секретне слово")
        elif self.license_manager.activate_license_key(word):
            self.activation_status.setText("Pro активовано (ключ)")
            self._append_log("Pro активовано через ліцензійний ключ")
        else:
            self.activation_status.setText("Помилка активації")
            self._append_log("Помилка активації")

    # ---- Макроси ----
    def init_macros_tab(self):
        layout = QVBoxLayout(self.macros_tab)
        btn_edit = QPushButton("Редагувати макроси")
        btn_edit.clicked.connect(self.open_macro_editor)
        layout.addWidget(btn_edit)
        self.macros_list = QTextEdit()
        self.macros_list.setReadOnly(True)
        layout.addWidget(self.macros_list)
        self._refresh_macros_list()

    def open_macro_editor(self):
        dialog = MacroDialog(self.config)
        if dialog.exec():
            self._refresh_macros_list()

    def _refresh_macros_list(self):
        macros = self.config.get("macros", [])
        text = "\n".join([f"{m['hotkey']} -> {m['message']}" for m in macros])
        self.macros_list.setPlainText(text)

    # ---- Налаштування ----
    def init_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.addWidget(QLabel("Тема оформлення:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["lava", "neon", "cyberpunk", "classic"])
        self.theme_combo.setCurrentText(self.current_theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        layout.addWidget(self.theme_combo)

        layout.addWidget(QLabel("Назва сервера:"))
        self.server_edit = QLineEdit(self.config.get("server_name", ""))
        layout.addWidget(self.server_edit)

        layout.addWidget(QLabel("Поріг черги:"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setValue(self.config.get("queue_threshold", 3))
        layout.addWidget(self.threshold_spin)

        btn_save = QPushButton("Зберегти")
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save)

    def save_settings(self):
        self.config.set("server_name", self.server_edit.text())
        self.config.set("queue_threshold", self.threshold_spin.value())
        self.config.set("theme", self.theme_combo.currentText())
        self.change_theme(self.theme_combo.currentText())
        self._append_log("Налаштування збережено")

    def change_theme(self, theme_name):
        self.apply_theme(theme_name)

    def apply_theme(self, theme_name):
        self.background.set_theme_colors(theme_name)
        qss_path = os.path.join("themes", f"{theme_name}.qss")
        if os.path.exists(qss_path):
            with open(qss_path, 'r') as f:
                self.setStyleSheet(f.read())
        else:
            self.setStyleSheet("")
        if theme_name == "lava":
            self.title_label.setStyleSheet("color: white;")
        elif theme_name == "neon":
            self.title_label.setStyleSheet("color: #00ffcc;")
        elif theme_name == "cyberpunk":
            self.title_label.setStyleSheet("color: #ff0099;")
        elif theme_name == "classic":
            self.title_label.setStyleSheet("color: black;")
        self.current_theme = theme_name

    # ---- Трей ----
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QApplication.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setToolTip("Arma Reforger Bot")
        tray_menu = QMenu()
        show_action = QAction("Показати вікно", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Вийти", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("Arma Reforger Bot", "Працює у фоновому режимі", QSystemTrayIcon.Information, 2000)

    # ---- Логування в GUI ----
    def _append_log(self, text):
        # Додає рядок у QTextEdit
        self.log_output.append(text)
        # Також пишемо в loguru (але воно вже пишеться окремо)
        logger.info(text)

    def add_log_handler(self):
        """Метод для підключення loguru до GUI через сигнал."""
        # Можна викликати після ініціалізації
        logger.add(lambda msg: self.log_signal.new_message.emit(str(msg)), level="INFO")

    # ---- Звукове сповіщення (для зовнішнього виклику) ----
    def play_sound(self, freq=1000, duration=200):
        if self.sound_enabled:
            winsound.Beep(freq, duration)