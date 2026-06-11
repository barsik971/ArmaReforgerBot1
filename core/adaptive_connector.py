import time
import json
import pyautogui
import pytesseract
from PIL import ImageGrab
import re
from pathlib import Path
from loguru import logger
from core.server_scanner import ServerScanner

class AdaptiveConnector:
    def __init__(self, config, game_controller):
        self.config = config
        self.game_ctrl = game_controller          # спільний об'єкт
        self.server_name = config.get("server_name", "Conflict in Europe #2")
        self.queue_threshold = config.get("queue_threshold", 3)
        self.max_queue_to_join = config.get("max_queue_to_join", 24)
        self.filter_positions = config.get("filter_positions", [])
        self.timeouts = config.get("timeouts", {
            "main_menu": 30, "multiplayer": 15, "favorites": 10,
            "server_list": 60, "queue": 300, "faction": 60, "in_game": 120
        })
        self.save_screenshots = config.get("save_screenshots", True)
        self.screenshots_dir = Path("training_data/screenshots")
        self.successful_profile_path = Path("training_data/successful_profile.json")
        self.scanner = ServerScanner(config)
        self.success_profile = self._load_success_profile()

    def connect(self):
        logger.info(f"🚀 Підключення до {self.server_name}")
        try:
            # 1. Переконатись, що гра запущена
            if not self.game_ctrl.is_game_running():
                if not self.game_ctrl.launch_game():
                    return False
                time.sleep(10)  # чекаємо ініціалізацію гри
            else:
                logger.info("Гра вже запущена")

            # 2. Перехід до улюбленого та вимкнення фільтрів
            self._navigate_to_favorites()
            self._disable_filters()

            # 3. Очікування доступності сервера та підключення
            self._wait_for_server_available()
            self._join_server()

            # 4. Черга сервера
            self._wait_for_server_queue()
            self._handle_server_queue()

            # 5. Черга фракції
            self._wait_for_faction_queue()
            self._handle_faction_and_deploy()

            self._learn_from_success()
            logger.info("✅ Гра завантажена")
            return True
        except Exception as e:
            logger.error(f"❌ Помилка підключення: {e}")
            self._save_failure_screenshot()
            return False

    # ---------- Навігація ----------
    def _navigate_to_favorites(self):
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

    def _wait_for_server_available(self):
        logger.info(f"Очікуємо доступність сервера '{self.server_name}'")
        max_wait = self.config.get("server_wait_timeout", 600)
        start = time.time()
        while time.time() - start < max_wait:
            players, max_players, queue = self.scanner.find_server_info(self.server_name)
            if players is None:
                logger.warning("Сервер не знайдено, оновлюю список")
                self.scanner.refresh_list()
                time.sleep(self.config.get("refresh_interval", 5))
                continue
            logger.info(f"Сервер: {players}/{max_players}, черга {queue}")
            if players < max_players and queue <= self.max_queue_to_join:
                logger.info("Сервер доступний")
                return
            self.scanner.refresh_list()
            time.sleep(self.config.get("refresh_interval", 5))
        raise TimeoutError("Не дочекались доступності сервера")

    def _join_server(self):
        pos = self.scanner.find_server_position(self.server_name)
        if pos:
            pyautogui.click(pos[0], pos[1])
            time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.press('enter')
        logger.info("Подвійний Enter відправлено")

    def _wait_for_server_queue(self):
        phrase = "Ви очікуєте в черзі сервера"  # з вашого скріншота
        self._wait_for_text(phrase, self.timeouts["queue"])

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

    def _wait_for_faction_queue(self):
        phrase = "Очікування вступу до фракції"  # ваш другий скріншот
        self._wait_for_text(phrase, self.timeouts["faction"])

    def _handle_faction_and_deploy(self):
        faction_pos = self.config.get("faction_ukraine_pos", (960, 540))
        deploy_pos = self.config.get("deploy_pos", (960, 700))
        pyautogui.click(faction_pos[0], faction_pos[1])
        time.sleep(0.5)
        pyautogui.click(deploy_pos[0], deploy_pos[1])

    def _learn_from_success(self):
        self._save_screenshot("success_final")

    # ---------- Допоміжні методи ----------
    def _wait_for_text(self, text, timeout):
        start = time.time()
        while time.time() - start < timeout:
            screen = ImageGrab.grab()
            screen_text = pytesseract.image_to_string(screen, lang='ukr+eng')
            if text.lower() in screen_text.lower():
                return
            time.sleep(2)
        raise TimeoutError(f"Не знайдено текст '{text}'")

    def _wait_for_state(self, state, timeout):
        start = time.time()
        while time.time() - start < timeout:
            if self._get_game_state() == state:
                return
            time.sleep(2)
        raise TimeoutError(f"Стан '{state}' не досягнуто")

    def _get_game_state(self):
        return self.game_ctrl.get_game_state()   # використовуємо GameController

    def _click_element(self, text):
        pos = self.scanner._ocr_find_word(text)
        if not pos:
            for d in (self.scanner.templates_dir, self.scanner.assets_dir):
                path = d / f"{text.lower().replace(' ', '_')}.png"
                if path.exists():
                    rect = self.scanner._find_image_on_screen(str(path))
                    if rect:
                        pos = (rect[0] + rect[2]//2, rect[1] + rect[3]//2)
                        break
        if pos:
            pyautogui.click(pos[0], pos[1])

    def _save_screenshot(self, prefix):
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        ImageGrab.grab().save(self.screenshots_dir / f"{prefix}_{timestamp}.png")

    def _save_failure_screenshot(self):
        self._save_screenshot("failure")

    def _load_success_profile(self):
        if self.successful_profile_path.exists():
            with open(self.successful_profile_path, 'r') as f:
                return json.load(f)
        return {
            "server_queue_phrase": "Ви очікуєте в черзі сервера",
            "faction_queue_phrase": "Очікування вступу до фракції",
            "actions": {}
        }