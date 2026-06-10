import hmac
import hashlib
from datetime import datetime
from loguru import logger

SIGNING_KEY = b"replace_with_strong_random_key_1234567890"

class LicenseManager:
    def __init__(self, config):
        self.config = config

    def is_pro(self) -> bool:
        if self.config.get("pro_activated", False):
            return True
        key = self.config.get("license_key", "")
        if key:
            return self.verify_license_key(key)
        return False

    def activate_secret(self, word: str) -> bool:
        if word == self.config.get("secret_word", ""):
            self.config.set("pro_activated", True)
            logger.info("Pro activated via secret word")
            return True
        return False

    def activate_license_key(self, license_key: str) -> bool:
        if self.verify_license_key(license_key):
            self.config.set("license_key", license_key)
            self.config.set("pro_activated", False)
            logger.info("Pro activated via license key")
            return True
        return False

    def verify_license_key(self, key: str) -> bool:
        try:
            parts = key.split(":")
            if len(parts) != 3:
                return False
            user_id, expiry_str, signature = parts
            data = f"{user_id}:{expiry_str}".encode()
            expected_signature = hmac.new(SIGNING_KEY, data, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_signature, signature):
                return False
            if expiry_str == "never":
                return True
            expiry_ts = int(expiry_str)
            return datetime.now().timestamp() < expiry_ts
        except Exception as e:
            logger.error(f"License verification error: {e}")
            return False

    def deactivate(self):
        self.config.set("license_key", "")
        self.config.set("license_expiry", "")
        self.config.set("pro_activated", False)
        logger.info("License deactivated")