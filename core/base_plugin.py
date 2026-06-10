from abc import ABC, abstractmethod

class BasePlugin(ABC):
    def __init__(self, config, game_controller):
        self.config = config
        self.game_controller = game_controller
        self._enabled = False

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    def is_enabled(self) -> bool:
        return self._enabled