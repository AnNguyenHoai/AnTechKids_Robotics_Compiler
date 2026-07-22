import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any

from . import config


class Plugin:
    def __init__(self, path: Path, metadata: Dict):
        self.path = path
        self.metadata = metadata
        self._module = None
        self._instance = None

    @property
    def name(self) -> str:
        return self.metadata.get('name', self.path.name)

    @property
    def type(self) -> str:
        return self.metadata.get('type', 'unknown')

    @property
    def entry(self) -> str:
        return self.metadata.get('entry', '')

    def load(self):
        """Load plugin module and instantiate entry class."""
        if not self.entry:
            raise ValueError(f"Plugin {self.name} missing entry point")
        module_path, class_name = self.entry.split(':')
        # Import module
        self._module = importlib.import_module(module_path)
        cls = getattr(self._module, class_name)
        self._instance = cls()
        return self._instance


def discover_plugins(plugin_type: str = None) -> List[Plugin]:
    """Discover all plugins in packages directory."""
    plugins = []
    packages_dir = config.ROOT / "packages"
    if not packages_dir.exists():
        return plugins
    for item in packages_dir.iterdir():
        if not item.is_dir():
            continue
        # Check for plugin.yaml or package.yaml with plugin section
        meta_file = item / "plugin.yaml"
        if not meta_file.exists():
            meta_file = item / "package.yaml"
        if not meta_file.exists():
            continue
        import yaml
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = yaml.safe_load(f)
        # Check if it's a plugin (has type, entry)
        if 'type' not in meta or 'entry' not in meta:
            continue
        if plugin_type and meta['type'] != plugin_type:
            continue
        plugins.append(Plugin(item, meta))
    return plugins