from core.base_plugin import BasePlugin
from loguru import logger
import time
import os
from datetime import datetime
from PIL import ImageGrab
import pytesseract

class OCRDataCollectorPlugin(BasePlugin):
    def get_name(self):
        return "Збір даних для OCR"

    def get_description(self):
        return "Зберігає скріншоти та розпізнаний текст у training_data"

    def on_enable(self):
        self.running = True
        self.thread = threading.Thread(target=self._collect, daemon=True)
        self.thread.start()
        logger.info("OCR data collector enabled")

    def on_disable(self):
        self.running = False
        logger.info("OCR data collector disabled")

    def _collect(self):
        while self.running:
            try:
                img = ImageGrab.grab()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img_path = f"training_data/screen_{timestamp}.png"
                os.makedirs("training_data", exist_ok=True)
                img.save(img_path)
                text = pytesseract.image_to_string(img)
                with open(f"training_data/text_{timestamp}.txt", "w") as f:
                    f.write(text)
                time.sleep(30)
            except Exception as e:
                logger.error(f"OCR collector error: {e}")