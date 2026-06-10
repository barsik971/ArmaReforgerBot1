import importlib
import pkgutil
import plugins
from pathlib import Path
from core.base_plugin import BasePlugin
from loguru import logger

class PluginManager:
    def __init__(self, config, game_controller, license_manager=None, main_window=None):
        """
        config: ConfigManager
        game_controller: GameController
        license_manager: LicenseManager (опціонально)
        main_window: MainWindow (опціонально, для плагінів, яким потрібне GUI)
        """
        self.config = config
        self.game_controller = game_controller
        self.license_manager = license_manager
        self.main_window = main_window
        self.plugins = {}

    def load_plugins(self):
        plugin_dir = Path(__file__).parent.parent / "plugins"
        for finder, name, ispkg in pkgutil.iter_modules([str(plugin_dir)]):
            if ispkg or name.startswith('_'):
                continue
            try:
                mod = importlib.import_module(f"plugins.{name}")
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                        instance = attr(self.config, self.game_controller)
                        # Передаємо посилання на головне вікно, якщо плагін це підтримує
                        if hasattr(instance, 'set_main_window') and self.main_window:
                            instance.set_main_window(self.main_window)
                        self.plugins[instance.get_name()] = instance
                        # Активуємо плагін, тільки якщо він був увімкнений і є Pro
                        if self.config.get_plugin_state(instance.get_name()):
                            if self.license_manager and self.license_manager.is_pro():
                                instance.on_enable()
                                instance._enabled = True
                            else:
                                # Якщо немає Pro – вимикаємо в конфігурації
                                self.config.set_plugin_state(instance.get_name(), False)
                        logger.info(f"Loaded plugin: {instance.get_name()}")
            except Exception as e:
                logger.error(f"Failed to load plugin {name}: {e}")

    def get_plugin_list(self):
        return list(self.plugins.values())

    def enable_plugin(self, name):
        if name in self.plugins:
            p = self.plugins[name]
            if not p.is_enabled():
                if self.license_manager and not self.license_manager.is_pro():
                    logger.warning("Pro required to enable plugin")
                    return False
                p.on_enable()
                p._enabled = True
                self.config.set_plugin_state(name, True)
                return True
        return False

    def disable_plugin(self, name):
        if name in self.plugins:
            p = self.plugins[name]
            if p.is_enabled():
                p.on_disable()
                p._enabled = False
                self.config.set_plugin_state(name, False)
                return True
        return False