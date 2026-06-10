import time
import json
import pyautogui
import pytesseract
from PIL import ImageGrab
import re
from pathlib import Path
from loguru import logger
from core.server_scanner import ServerScanner
import subprocess

class AdaptiveConnector:
    def __init__(self, config):
        self.config = config
        self.server_name = config.get("server_name", "Conflict in Europe #2")
        self.queue_threshold = config.get("queue_threshold", 3)
        self.max_queue_to_join = config.get("max_queue_to_join", 24)
        self.filter_positions = config.get("filter_positions", [])
        self.successful_profile_path = Path("training_data/successful_profile.json")
        self.screenshots_dir = Path("training_data/screenshots")
        self.timeouts = config.get("timeouts", {
            "main_menu": 30, "multiplayer": 15, "favorites": 10,
            "server_list": 60, "queue": 300, "faction": 60, "in_game": 120
        })
        self.save_screenshots = config.get("save_screenshots", True)
        self.refresh_key = config.get("refresh_key", "r")
        self.refresh_interval = config.get("refresh_interval", 5)

        self.scanner = ServerScanner(config)
        self.success_profile = self._load_success_profile()

    # ---------- Профіль успіху ----------
    def _load_success_profile(self):
        if self.successful_profile_path.exists():
            try:
                with open(self.successful_profile_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "server_queue_phrase": "Ви очікуєте в черзі сервера",
            "faction_queue_phrase": "Очікування вступу до фракції",
            "actions": {}
        }

    def _save_success_profile(self):
        self.successful_profile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.successful_profile_path, 'w') as f:
            json.dump(self.success_profile, f, indent=2)

    def _tesseract_available(self):
        """Перевіряє, чи встановлено tesseract і чи доступний він через PATH."""
        try:
            subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
            return True
        except:
            return False

    # ---------- Головний цикл ----------
    def connect(self):
        if not self._tesseract_available():
            logger.error("Tesseract не знайдено. OCR-функції недоступні.")
            return False

        logger.info(f"🚀 Підключення до {self.server_name}")
        try:
            self._navigate_to_favorites()
            self._disable_filters()
            self._wait_for_server_available()
            self._join_server()
            self._wait_for_server_queue()
            self._handle_server_queue()
            self._wait_for_faction_queue()
            self._handle_faction_and_deploy()
            self._learn_from_success()
            logger.info("✅ Гра завантажена")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка: {e}")
            self._save_failure_screenshot()
            return False

    # ---------- Навігація ----------
    def _navigate_to_favorites(self):
        logger.debug("Мультиплеєр → Улюблене")
        self._wait_for_state("main_menu", self.timeouts["main_menu"])
        self._click_element("MULTIPLAYER")
        time.sleep(2)
        self._wait_for_state("multiplayer", self.timeouts["multiplayer"])
        self._click_element("FAVORITES")
        time.sleep(1)

    def _disable_filters(self):
        if not self.filter_positions:
            return
        for x, y in self.filter_positions:
            pyautogui.click(x, y)
            time.sleep(0.2)

    # ---------- Очікування доступності ----------
    def _wait_for_server_available(self):
        logger.debug(f"Очікуємо доступність сервера '{self.server_name}'")
        max_wait = self.config.get("server_wait_timeout", 600)
        start = time.time()

        while time.time() - start < max_wait:
            players, max_players, queue = self.scanner.find_server_info(self.server_name)
            if players is None:
                logger.warning("Сервер не знайдено в списку. Оновлюю...")
                self.scanner.refresh_list()
                time.sleep(self.refresh_interval)
                continue

            logger.info(f"Сервер: {players}/{max_players}, черга: {queue}")
            if players < max_players and queue <= self.max_queue_to_join:
                logger.info("✅ Сервер доступний")
                return
            else:
                logger.info("Сервер недоступний. Оновлюю список...")
                self.scanner.refresh_list()
                time.sleep(self.refresh_interval)
        raise TimeoutError("Не дочекались доступності сервера")

    # ---------- Підключення ----------
    def _join_server(self):
        pos = self.scanner.find_server_position(self.server_name)
        if pos:
            pyautogui.click(pos[0], pos[1])
            time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.press('enter')
        logger.info("Подвійний Enter відправлено")

    # ---------- Черга сервера ----------
    def _wait_for_server_queue(self):
        self._wait_for_text_on_screen(
            self.success_profile["server_queue_phrase"],
            self.timeouts["queue"]
        )

    def _handle_server_queue(self):
        while True:
            pos = self._get_queue_number()
            logger.info(f"Місце в черзі сервера: {pos}")
            if pos <= self.queue_threshold:
                break
            time.sleep(5)
        self._click_element("OK")

    def _get_queue_number(self):
        screen = ImageGrab.grab()
        text = pytesseract.image_to_string(screen, lang='ukr+eng')
        match = re.search(r'Місце у черзі:\s*(\d+)', text)
        if not match:
            match = re.search(r'Place in queue:\s*(\d+)', text, re.IGNORECASE)
        return int(match.group(1)) if match else 999

    # ---------- Черга фракції ----------
    def _wait_for_faction_queue(self):
        self._wait_for_text_on_screen(
            self.success_profile["faction_queue_phrase"],
            self.timeouts["faction"]
        )

    def _handle_faction_and_deploy(self):
        faction_pos = self.config.get("faction_ukraine_pos", (960, 540))
        deploy_pos = self.config.get("deploy_pos", (960, 700))
        pyautogui.click(faction_pos[0], faction_pos[1])
        time.sleep(0.5)
        pyautogui.click(deploy_pos[0], deploy_pos[1])

    # ---------- Навчання ----------
    def _learn_from_success(self):
        self._save_screenshot("success_final")

    # ---------- Допоміжні методи ----------
    def _wait_for_text_on_screen(self, text, timeout):
        start = time.time()
        while time.time() - start < timeout:
            screen = ImageGrab.grab()
            screen_text = pytesseract.image_to_string(screen, lang='ukr+eng')
            if text.lower() in screen_text.lower():
                return
            time.sleep(2)
        raise TimeoutError(f"Не знайдено '{text}'")

    def _click_element(self, text):
        # Спочатку спробуємо знайти як шаблон
        for directory in (self.scanner.templates_dir, self.scanner.assets_dir):
            path = directory / f"{text.lower().replace(' ', '_')}.png"
            if path.exists():
                rect = self._find_image_on_screen(str(path))
                if rect:
                    pos = (rect[0] + rect[2]//2, rect[1] + rect[3]//2)
                    pyautogui.click(pos[0], pos[1])
                    return
        # Потім OCR
        pos = self.scanner._ocr_find_word(text)
        if pos:
            pyautogui.click(pos[0], pos[1])
        else:
            logger.warning(f"Не знайдено '{text}' для кліку")

    def _find_image_on_screen(self, image_path, confidence=0.8):
        return self.scanner._find_image_on_screen(image_path, confidence)

    def _save_screenshot(self, prefix):
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        ImageGrab.grab().save(self.screenshots_dir / f"{prefix}_{timestamp}.png")

    def _save_failure_screenshot(self):
        self._save_screenshot("failure")

    def _get_game_state(self):
        screen = ImageGrab.grab()
        text = pytesseract.image_to_string(screen, lang='eng').lower()
        if "main menu" in text:
            return "main_menu"
        if "multiplayer" in text and "favorites" not in text:
            return "multiplayer"
        return "unknown"

    def _wait_for_state(self, state, timeout):
        start = time.time()
        while time.time() - start < timeout:
            if self._get_game_state() == state:
                return
            time.sleep(2)
        raise TimeoutError(f"Стан {state} не досягнуто")