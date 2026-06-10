import os
import time
from pathlib import Path
from core.base_plugin import BasePlugin
from loguru import logger
import pyautogui
from PIL import ImageGrab
from PySide6.QtCore import QTimer

class DatasetCollectorPlugin(BasePlugin):
    def get_name(self):
        return "Збір датасету (Trainer)"

    def get_description(self):
        return "Записує еталонні зображення кнопок та координати для покращення розпізнавання"

    def on_enable(self):
        self.dataset_dir = Path("training_data/templates")
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.actions_dir = Path("training_data/actions")
        self.actions_dir.mkdir(parents=True, exist_ok=True)
        # Налаштовуємо гарячу клавішу (наприклад, Ctrl+Shift+R) через keyboard
        try:
            import keyboard
            keyboard.add_hotkey('ctrl+shift+r', self.capture_template)
            logger.info("Hotkey Ctrl+Shift+R registered for template capture")
        except ImportError:
            logger.warning("keyboard module not installed, hotkey disabled")
        # Також можна активувати через GUI, але поки через консоль/хоткей
        self._enabled = True
        logger.info("DatasetCollector enabled. Press Ctrl+Shift+R to capture a template.")

    def on_disable(self):
        try:
            import keyboard
            keyboard.remove_hotkey('ctrl+shift+r')
        except:
            pass
        logger.info("DatasetCollector disabled")

    def capture_template(self):
        """Захоплює область навколо курсора як шаблон."""
        # Отримуємо позицію миші
        x, y = pyautogui.position()
        # Захоплюємо невелику область навколо (наприклад, 80x30 пікселів)
        region = (x-40, y-15, 80, 30)
        img = ImageGrab.grab(bbox=region)
        # Запитуємо у користувача назву шаблону (в консолі)
        # В реальному GUI можна показати діалог, але тут використовуємо input
        print(f"Захоплено область {region}. Введіть назву шаблону (напр. server_row, join_btn):")
        name = input().strip()
        if not name:
            name = f"template_{int(time.time())}"
        filepath = self.dataset_dir / f"{name}.png"
        img.save(filepath)
        # Зберігаємо також координати кліку відносно лівого верхнього кута області
        coord_file = self.actions_dir / f"{name}.txt"
        with open(coord_file, 'w') as f:
            f.write(f"click_rel_x: {x - region[0]}\nclick_rel_y: {y - region[1]}\n")
        logger.info(f"Template '{name}' saved to {filepath}")

    def get_settings_widget(self):
        # Можна додати кнопку в GUI, але це вимагає інтеграції з MainWindow
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
        w = QWidget()
        layout = QVBoxLayout(w)
        btn = QPushButton("Захопити шаблон (Ctrl+Shift+R)")
        btn.clicked.connect(self.capture_template)
        layout.addWidget(btn)
        return w