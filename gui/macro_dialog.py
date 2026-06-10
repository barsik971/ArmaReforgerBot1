from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton,
                               QHBoxLayout, QLabel, QLineEdit)
from loguru import logger

class MacroDialog(QDialog):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Редактор макросів")
        layout = QVBoxLayout()
        self.macros = config.get("macros", [])
        self.list_widget = QTextEdit()
        self.list_widget.setReadOnly(True)
        self.refresh_list()
        layout.addWidget(self.list_widget)

        add_layout = QHBoxLayout()
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("Гаряча клавіша (напр. ctrl+1)")
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Повідомлення")
        add_layout.addWidget(QLabel("Клавіша:"))
        add_layout.addWidget(self.hotkey_edit)
        add_layout.addWidget(QLabel("Текст:"))
        add_layout.addWidget(self.message_edit)
        btn_add = QPushButton("Додати")
        btn_add.clicked.connect(self.add_macro)
        add_layout.addWidget(btn_add)
        layout.addLayout(add_layout)

        btn_close = QPushButton("Закрити")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        self.setLayout(layout)

    def refresh_list(self):
        text = ""
        for i, macro in enumerate(self.macros):
            text += f"{macro['hotkey']} -> {macro['message']}\n"
        self.list_widget.setPlainText(text)

    def add_macro(self):
        hotkey = self.hotkey_edit.text().strip()
        message = self.message_edit.text().strip()
        if hotkey and message:
            self.macros.append({"hotkey": hotkey, "message": message})
            self.config.set("macros", self.macros)
            self.refresh_list()
            self.hotkey_edit.clear()
            self.message_edit.clear()