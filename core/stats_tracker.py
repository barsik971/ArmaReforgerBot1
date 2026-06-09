# Модуль для запису статистики бою (kills, deaths, score). Використовується плагіном.
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

class StatsTracker:
    def __init__(self, file="stats.json"):
        self.file = Path(file)
        self.data = self._load()

    def _load(self):
        if self.file.exists():
            with open(self.file, 'r') as f:
                return json.load(f)
        return []

    def save(self):
        with open(self.file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add_record(self, kills: int, deaths: int, score: int):
        record = {
            "timestamp": datetime.now().isoformat(),
            "kills": kills,
            "deaths": deaths,
            "score": score
        }
        self.data.append(record)
        self.save()
        logger.info(f"Stats recorded: {record}")