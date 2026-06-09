import importlib
import pkgutil
import plugins as plugin_pkg
from pathlib import Path
from core.base_plugin import BasePlugin
from loguru import logger

class PluginManager:
    def __init__(self, config, game_controller):
        self.config = config
        self.game_controller = game_controller
        self.plugins = {}  # name -> instance

    def load_plugins(self):
        # Динамічне завантаження з папки plugins/
        plugin_dir = Path(__file__).parent.parent / "plugins"
        for finder, name, ispkg in pkgutil.iter_modules([str(plugin_dir)]):
            if ispkg:
                continue
            try:
                mod = importlib.import_module(f"plugins.{name}")
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                        plugin_instance = attr(self.config, self.game_controller)
                        self.plugins[plugin_instance.get_name()] = plugin_instance
                        # Активувати, якщо збережено в конфігурації
                        if self.config.get_plugin_state(plugin_instance.get_name()):
                            if not plugin_instance.is_enabled():
                                plugin_instance.on_enable()
                                plugin_instance._enabled = True
                        logger.info(f"Loaded plugin: {plugin_instance.get_name()}")
            except Exception as e:
                logger.error(f"Failed to load plugin {name}: {e}")

    def get_plugin_list(self):
        return list(self.plugins.values())

    def enable_plugin(self, name):
        if name in self.plugins:
            plugin = self.plugins[name]
            if not plugin.is_enabled():
                plugin.on_enable()
                plugin._enabled = True
                self.config.set_plugin_state(name, True)
                return True
        return False

    def disable_plugin(self, name):
        if name in self.plugins:
            plugin = self.plugins[name]
            if plugin.is_enabled():
                plugin.on_disable()
                plugin._enabled = False
                self.config.set_plugin_state(name, False)
                return True
        return False