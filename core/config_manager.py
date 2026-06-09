import json
from pathlib import Path
from typing import Any

class ConfigManager:
    def __init__(self, path: Path):
        self.path = path
        self.defaults = {
            "server_name": "MyServer",
            "queue_threshold": 3,
            "filter_positions": [(100, 200), (150, 250)],
            "sound_enabled": True,
            "theme": "lava",
            "plugins": {},
            "telegram_token": "",
            "telegram_enabled": True,
            "pro_activated": False,
            "license_key": "",
            "license_expiry": "",
            "secret_word": "MySuperSecret2025",
            "macros": [],
            "schedule": {}
        }
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self.defaults.copy()

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default=None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

    def get_plugin_state(self, plugin_name: str) -> bool:
        return self.data.get("plugins", {}).get(plugin_name, False)

    def set_plugin_state(self, plugin_name: str, enabled: bool):
        if "plugins" not in self.data:
            self.data["plugins"] = {}
        self.data["plugins"][plugin_name] = enabled
        self.save()