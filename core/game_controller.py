import subprocess
import time
import pyautogui
import pytesseract
from PIL import ImageGrab
import psutil
from loguru import logger

class GameController:
    def __init__(self, config):
        self.config = config
        tesseract_path = config.get("tesseract_path", None)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.game_exe_path = config.get("game_exe_path", None)
        self.steam_appid = config.get("steam_appid", None)
        self.launch_timeout = config.get("game_launch_timeout", 60)

    def is_game_running(self) -> bool:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'ArmaReforger' in proc.info['name']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def launch_game(self):
        if self.is_game_running():
            logger.info("Гра вже запущена")
            return True
        logger.info("Запускаємо гру...")
        try:
            if self.steam_appid:
                subprocess.Popen(f"start steam://rungameid/{self.steam_appid}", shell=True)
            elif self.game_exe_path:
                subprocess.Popen([self.game_exe_path], shell=True)
            else:
                logger.error("Не вказано шлях до гри в config.json")
                return False
            waited = 0
            while waited < self.launch_timeout:
                if self.is_game_running():
                    logger.info("Гра успішно запущена")
                    return True
                time.sleep(2)
                waited += 2
            logger.error("Не вдалося дочекатися запуску гри")
            return False
        except Exception as e:
            logger.error(f"Помилка запуску гри: {e}")
            return False

    def get_game_state(self) -> str:
        if not self.is_game_running():
            return "not_running"
        try:
            # Не робимо скріншот, якщо Tesseract не налаштований
            if not hasattr(self, '_tesseract_checked'):
                self._tesseract_ok = self._check_tesseract()
                self._tesseract_checked = True
            if not self._tesseract_ok:
                return "unknown"
            screen = ImageGrab.grab()
            text = pytesseract.image_to_string(screen, lang='ukr+eng').lower()
            if "головне меню" in text or "main menu" in text:
                return "main_menu"
            if "мультиплеєр" in text or "multiplayer" in text:
                return "multiplayer"
            if "улюблене" in text or "favorites" in text:
                return "favorites"
            if "сервер" in text and ("браузер" in text or "browser" in text):
                return "server_list"
            if "черга" in text and ("місце" in text or "position" in text):
                return "queue"
            if "очікування вступу" in text or "faction" in text:
                return "faction"
            if "deploy" in text or "в бій" in text:
                return "in_game"
            return "unknown"
        except Exception as e:
            logger.error(f"OCR помилка: {e}")
            return "unknown"

    def _check_tesseract(self):
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False

    # Заглушки для сумісності
    def click_filter_positions(self):
        positions = self.config.get("filter_positions", [])
        for x, y in positions:
            pyautogui.click(x, y)
            time.sleep(0.1)

    def connect_to_server(self, server_name: str):
        pass

    def is_queue_below_threshold(self, threshold: int) -> bool:
        return True

    def get_queue_position(self) -> int:
        return 0