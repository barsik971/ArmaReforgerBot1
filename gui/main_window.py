import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QTextEdit, QSpinBox, QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QAction, QIcon, QPainter, QLinearGradient, QColor, QFont
from loguru import logger
from core.license_manager import LicenseManager
from core.plugin_manager import PluginManager
from core.game_controller import GameController
from core.telegram_bot import TelegramBot
from gui.macro_dialog import MacroDialog
from gui.calibration_wizard import CalibrationWizard
import winsound

class AnimatedBackground(QWidget):
    """Віджет з анімованим градієнтним фоном."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        self.angle = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        self.angle = (self.angle + 1) % 360
        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        # Лавові тони
        gradient.setColorAt(0.0, QColor(255, 80, 0))
        gradient.setColorAt(0.5, QColor(200, 0, 200))
        gradient.setColorAt(1.0, QColor(0, 200, 255))
        # Зміщення кута для анімації
        painter.setBrush(gradient)
        painter.drawRect(rect)

class MainWindow(QMainWindow):
    def __init__(self, config, license_manager, plugin_manager, game_controller, telegram_bot):
        super().__init__()
        self.config = config
        self.license_manager = license_manager
        self.plugin_manager = plugin_manager
        self.game_controller = game_controller
        self.telegram_bot = telegram_bot
        self.setWindowTitle("Arma Reforger Auto Bot")
        self.setGeometry(100, 100, 900, 700)

        # Анімований фон
        self.background = AnimatedBackground(self)
        self.setCentralWidget(self.background)

        # Основний шар поверх фону
        main_widget = QWidget(self.background)
        main_layout = QVBoxLayout(main_widget)
        main_widget.setStyleSheet("background: transparent;")

        # Заголовок
        title = QLabel("Arma Reforger Auto Bot")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: white;")
        main_layout.addWidget(title)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { background: rgba(0,0,0,120); }")
        main_layout.addWidget(self.tabs)

        # Вкладка "Головна"
        self.dashboard_tab = QWidget()
        self.tabs.addTab(self.dashboard_tab, "Головна")
        self.init_dashboard_tab()

        # Вкладка "Плагіни"
        self.plugins_tab = QWidget()
        self.tabs.addTab(self.plugins_tab, "Плагіни")
        self.init_plugins_tab()

        # Вкладка "Активація"
        self.activation_tab = QWidget()
        self.tabs.addTab(self.activation_tab, "Активація")
        self.init_activation_tab()

        # Вкладка "Макроси"
        self.macros_tab = QWidget()
        self.tabs.addTab(self.macros_tab, "Макроси")
        self.init_macros_tab()

        # Вкладка "Налаштування"
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Налаштування")
        self.init_settings_tab()

        # Логування
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        self.log_output.setStyleSheet("background: rgba(0,0,0,180); color: #0f0;")
        main_layout.addWidget(QLabel("Лог:"))
        main_layout.addWidget(self.log_output)

        # Трей-іконка
        self.init_tray()

        # Звукові сповіщення (можна викликати з інших місць)
        self.sound_enabled = config.get("sound_enabled", True)

        # Підключення логування до віджету
        logger.add(self._log_to_gui, level="INFO")

        # Застосувати поточну тему
        self.apply_theme(config.get("theme", "lava"))

    def _log_to_gui(self, message):
        # Це хендлер для loguru, але він очікує словник. Зробимо простіше: використовувати сигнал
        pass

    def init_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        layout.addWidget(QLabel("Стан гри: невідомо"))
        layout.addWidget(QLabel("Черга сервера: N/A"))
        # Прогрес-бар черги (заповнюється з плагіна queue_progress_bar)
        from PySide6.QtWidgets import QProgressBar
        self.server_queue_bar = QProgressBar()
        self.server_queue_bar.setMaximum(100)
        layout.addWidget(QLabel("Прогрес черги сервера:"))
        layout.addWidget(self.server_queue_bar)
        self.faction_queue_bar = QProgressBar()
        layout.addWidget(QLabel("Черга фракції:"))
        layout.addWidget(self.faction_queue_bar)
        # Кнопки керування автоматизацією
        btn_start = QPushButton("Запустити авто")
        btn_stop = QPushButton("Зупинити авто")
        layout.addWidget(btn_start)
        layout.addWidget(btn_stop)

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
            desc.setStyleSheet("color: gray;")
            layout.addWidget(desc)

    def toggle_plugin(self, plugin, state):
        if state:
            self.plugin_manager.enable_plugin(plugin.get_name())
        else:
            self.plugin_manager.disable_plugin(plugin.get_name())

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
        else:
            # Спроба активації ключем (days=0 для безстрокового)
            self.license_manager.activate_license_key(word, 0)
            if self.license_manager.is_pro():
                self.activation_status.setText("Pro активовано (ключ)")
            else:
                self.activation_status.setText("Помилка активації")

    def init_macros_tab(self):
        layout = QVBoxLayout(self.macros_tab)
        btn_edit = QPushButton("Редагувати макроси")
        btn_edit.clicked.connect(self.open_macro_editor)
        layout.addWidget(btn_edit)
        self.macros_list = QTextEdit()
        self.macros_list.setReadOnly(True)
        layout.addWidget(self.macros_list)

    def open_macro_editor(self):
        dialog = MacroDialog(self.config)
        dialog.exec()

    def init_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        # Тема
        layout.addWidget(QLabel("Тема оформлення:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["lava", "neon", "cyberpunk", "classic"])
        self.theme_combo.setCurrentText(self.config.get("theme", "lava"))
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        layout.addWidget(self.theme_combo)

        # Назва сервера
        layout.addWidget(QLabel("Назва сервера:"))
        self.server_edit = QLineEdit(self.config.get("server_name", ""))
        layout.addWidget(self.server_edit)

        # Поріг черги
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
        self.apply_theme(self.theme_combo.currentText())

    def change_theme(self, theme):
        self.apply_theme(theme)

    def apply_theme(self, theme_name):
        qss_path = os.path.join("themes", f"{theme_name}.qss")
        if os.path.exists(qss_path):
            with open(qss_path, 'r') as f:
                self.setStyleSheet(f.read())
        else:
            self.setStyleSheet("")

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        #  self.tray_icon.setIcon(QIcon("icon.ico"))  # потребує файл іконки
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
        # Згортання в трей
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("Arma Reforger Bot", "Працює у фоновому режимі", QSystemTrayIcon.Information, 2000)

    def play_sound(self, freq=1000, duration=200):
        if self.sound_enabled:
            winsound.Beep(freq, duration)