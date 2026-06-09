from core.base_plugin import BasePlugin
from loguru import logger
import keyboard
import threading

class MacrosPlugin(BasePlugin):
    def get_name(self):
        return "Макроси для чату"

    def get_description(self):
        return "Надсилає збережені повідомлення за гарячими клавішами"

    def on_enable(self):
        self.macros = self.config.get("macros", [])
        for macro in self.macros:
            hotkey = macro['hotkey']
            keyboard.add_hotkey(hotkey, self.send_message, args=(macro['message'],))
        logger.info("Macros enabled")

    def on_disable(self):
        keyboard.unhook_all()
        logger.info("Macros disabled")

    def send_message(self, message):
        # Надсилання повідомлення в чат гри (емуляція вводу)
        import pyautogui
        pyautogui.press('t')  # Відкрити чат
        pyautogui.write(message, interval=0.02)
        pyautogui.press('enter')