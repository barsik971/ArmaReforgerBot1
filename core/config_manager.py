import json
from pathlib import Path
from typing import Any

class ConfigManager:
    def __init__(self, path: Path):
        self.path = path
        self.defaults = {
            "server_name": "MyServer",
            "queue_threshold": 3,
            "max_queue_to_join": 24,
            "filter_positions": [[100, 200], [150, 250]],
            "server_list_region": [0, 150, 1920, 900],
            "scroll_amount": -5,
            "max_scroll_attempts": 20,
            "refresh_key": "r",
            "refresh_interval": 5,
            "server_wait_timeout": 600,
            "timeouts": {
                "main_menu": 30, "multiplayer": 15, "favorites": 10,
                "server_list": 60, "queue": 300, "faction": 60, "in_game": 120
            },
            "faction_ukraine_pos": [960, 540],
            "deploy_pos": [960, 700],
            "save_screenshots": True,
            "sound_enabled": True,
            "theme": "lava",
            "plugins": {},
            "telegram_token": "",
            "telegram_enabled": True,
            "admin_chat_id": 390469052,
            "pro_activated": False,
            "license_key": "",
            "license_expiry": "",
            "secret_word": "MySuperSecret2025",
            "macros": [],
            "schedule": {},
            "monitored_servers": [],
            "monitor_interval": 30,
            "webapp_url": "http://localhost:5000"
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