import time
import pyautogui
import pytesseract
from PIL import ImageGrab, Image
import cv2
import numpy as np
import re
from pathlib import Path
from loguru import logger

class ServerConnector:
    def __init__(self, config):
        self.config = config
        self.server_name = config.get("server_name", "Conflict in Europe #2")
        self.queue_threshold = config.get("queue_threshold", 3)
        self.filter_positions = config.get("filter_positions", [])
        self.assets_dir = Path("assets")
        self.templates_dir = Path("training_data/templates")   # папка з вирізаними зразками кнопок
        self.save_screenshots = config.get("save_screenshots", False)
        self.screenshots_dir = Path("training_data/screenshots")
        self.server_list_region = config.get("server_list_region", (0, 150, 1920, 900))
        self.scroll_amount = config.get("scroll_amount", -5)
        self.scroll_pause = 0.5
        self.max_scroll_attempts = config.get("max_scroll_attempts", 20)
        self.timeouts = config.get("timeouts", {
            "main_menu": 30, "multiplayer": 15, "favorites": 10,
            "server_list": 60, "queue": 300, "faction": 60, "in_game": 120
        })

    def connect(self):
        logger.info(f"Starting connection to server: {self.server_name}")
        try:
            self._navigate_to_favorites()
            self._disable_filters()
            self._select_server_and_connect()
            self._handle_queue_and_faction()
            logger.info("✅ Successfully connected to the game!")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    def _navigate_to_favorites(self):
        logger.debug("Navigating to Favorites...")
        self._wait_for_state("main_menu", self.timeouts["main_menu"])
        self._click_text_or_image("MULTIPLAYER")
        time.sleep(2)
        self._wait_for_state("multiplayer", self.timeouts["multiplayer"])
        self._click_text_or_image("FAVORITES")
        time.sleep(1)
        self._wait_for_state("favorites", self.timeouts["favorites"])

    def _disable_filters(self):
        if not self.filter_positions:
            return
        logger.debug("Disabling filters...")
        for x, y in self.filter_positions:
            pyautogui.click(x, y)
            time.sleep(0.2)
        logger.info("Filters disabled")

    def _select_server_and_connect(self):
        logger.debug(f"Searching for server: {self.server_name}")
        found = False
        for scroll_attempt in range(self.max_scroll_attempts):
            screen = ImageGrab.grab(bbox=self.server_list_region)
            text = pytesseract.image_to_string(screen, lang='eng')
            if self.server_name.lower() in text.lower():
                found = True
                logger.info(f"Server found on screen after {scroll_attempt} scrolls")
                break
            pyautogui.scroll(self.scroll_amount)
            time.sleep(self.scroll_pause)

        if not found:
            raise Exception(f"Server '{self.server_name}' not found in list after scrolling")

        # Шукаємо сервер спочатку через зображення з датасету, потім OCR
        server_pos = self._locate_with_dataset("server_row")  # спроба знайти рядок сервера по зразку
        if not server_pos:
            server_pos = self._ocr_find_word(self.server_name, region=self.server_list_region)
        if not server_pos:
            # Остання спроба – зображення з assets
            server_img = self.assets_dir / "server_name.png"
            if server_img.exists():
                rect = self._find_image_on_screen(str(server_img), confidence=0.8)
                if rect:
                    server_pos = (rect[0] + rect[2]//2, rect[1] + rect[3]//2)
        if not server_pos:
            raise Exception("Could not locate server on screen")

        pyautogui.click(server_pos[0], server_pos[1])
        logger.info(f"Server selected at {server_pos}")
        time.sleep(0.5)

        # Приєднуємось подвійним Enter
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.press('enter')
        logger.info("Join sequence completed")

    def _handle_queue_and_faction(self):
        self._wait_for_state("queue", self.timeouts["queue"])
        while True:
            queue_pos = self._get_queue_position()
            logger.info(f"Queue position: {queue_pos}")
            if queue_pos <= self.queue_threshold:
                break
            time.sleep(5)
        # Натискаємо OK
        ok_pos = self._locate_with_dataset("ok_button") or self._ocr_find_word("OK", region=(800, 600, 400, 200))
        if ok_pos:
            pyautogui.click(ok_pos[0], ok_pos[1])
            logger.info("Clicked OK")
        time.sleep(5)
        if self._get_game_state() == "faction":
            self._select_faction()
        self._wait_for_state("in_game", self.timeouts["in_game"])

    def _select_faction(self):
        faction_pos = self.config.get("faction_click_pos", (960, 540))
        deploy_pos = self.config.get("deploy_click_pos", (960, 700))
        pyautogui.click(faction_pos[0], faction_pos[1])
        time.sleep(1)
        pyautogui.click(deploy_pos[0], deploy_pos[1])

    # ---------- Утиліти розпізнавання з використанням датасету ----------
    def _locate_with_dataset(self, template_name):
        """Шукає зображення з training_data/templates/ або assets/."""
        # Пріоритет: training_data/templates/ -> assets/ -> None
        for directory in (self.templates_dir, self.assets_dir):
            path = directory / f"{template_name}.png"
            if path.exists():
                rect = self._find_image_on_screen(str(path), confidence=0.8)
                if rect:
                    return (rect[0] + rect[2]//2, rect[1] + rect[3]//2)
        return None

    def _find_image_on_screen(self, image_path, confidence=0.8, region=None):
        try:
            screen = np.array(ImageGrab.grab(bbox=region)) if region else np.array(ImageGrab.grab())
            template = cv2.imread(image_path)
            if template is None:
                return None
            h, w = template.shape[:2]
            res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val >= confidence:
                return (max_loc[0], max_loc[1], w, h)
        except Exception as e:
            logger.error(f"Image matching error: {e}")
        return None

    def _ocr_find_word(self, word, region=None):
        img = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
        if self.save_screenshots:
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            img.save(self.screenshots_dir / f"ocr_{timestamp}.png")
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        for i, text in enumerate(data['text']):
            if word.lower() in text.lower():
                x = data['left'][i] + data['width'][i] // 2
                y = data['top'][i] + data['height'][i] // 2
                if region:
                    x += region[0]
                    y += region[1]
                return (x, y)
        return None

    def _get_game_state(self):
        try:
            screen = ImageGrab.grab()
            text = pytesseract.image_to_string(screen, lang='eng').lower()
            if "main menu" in text:
                return "main_menu"
            if "multiplayer" in text and "favorites" not in text:
                return "multiplayer"
            if "favorites" in text:
                return "favorites"
            if "server browser" in text or "servers" in text:
                return "server_list"
            if "queue" in text and "position" in text:
                return "queue"
            if "deploy" in text or "spawn" in text:
                return "in_game"
            return "unknown"
        except:
            return "unknown"

    def _wait_for_state(self, desired_state, timeout):
        start = time.time()
        while time.time() - start < timeout:
            if self._get_game_state() == desired_state:
                return
            time.sleep(2)
        raise TimeoutError(f"Timed out waiting for state '{desired_state}'")

    def _get_queue_position(self) -> int:
        try:
            screen = ImageGrab.grab()
            text = pytesseract.image_to_string(screen, lang='eng')
            match = re.search(r'queue:\s*(\d+)', text, re.IGNORECASE)
            return int(match.group(1)) if match else 999
        except:
            return 999

    def _click_text_or_image(self, text):
        # Використовуємо новий метод
        pos = self._locate_with_dataset(text.lower().replace(' ', '_'))
        if not pos:
            pos = self._ocr_find_word(text)
        if pos:
            pyautogui.click(pos[0], pos[1])
        else:
            logger.warning(f"Could not find '{text}'")