from datetime import datetime, timedelta
from loguru import logger

class LicenseManager:
    def __init__(self, config):
        self.config = config

    def is_pro(self) -> bool:
        # Секретне слово активує Pro назавжди
        if self.config.get("pro_activated", False):
            return True
        # Перевірка ліцензійного ключа
        key = self.config.get("license_key", "")
        expiry = self.config.get("license_expiry", "")
        if key and expiry:
            try:
                exp_date = datetime.strptime(expiry, "%Y-%m-%d")
                if exp_date > datetime.now():
                    return True
            except:
                pass
        return False

    def activate_secret(self, word: str) -> bool:
        if word == self.config.get("secret_word", ""):
            self.config.set("pro_activated", True)
            logger.info("Pro activated via secret word")
            return True
        return False

    def activate_license_key(self, key: str, days: int):
        # Додає ключ та дату закінчення (0 = назавжди)
        if days == 0:
            expiry = "2099-12-31"
        else:
            expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        self.config.set("license_key", key)
        self.config.set("license_expiry", expiry)
        self.config.set("pro_activated", False)
        logger.info(f"License activated until {expiry}")
        return True

    def deactivate(self):
        self.config.set("license_key", "")
        self.config.set("license_expiry", "")
        self.config.set("pro_activated", False)
        logger.info("License deactivated")