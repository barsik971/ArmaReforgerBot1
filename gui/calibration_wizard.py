from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class CalibrationWizard(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калібрування координат")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Калібрування поки що не реалізовано"))
        btn = QPushButton("ОК")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        self.setLayout(layout)