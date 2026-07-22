"""
Language Loader.

Responsibility: Load api.yaml and build RobotLanguage model.
"""

import yaml
from pathlib import Path
from .model import RobotLanguage
from .exceptions import SpecificationError


class LanguageLoader:
    @staticmethod
    def load(filepath: Path) -> RobotLanguage:
        """Load specification from YAML file."""
        if not filepath.exists():
            raise SpecificationError(f"Specification file not found: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SpecificationError(f"Invalid YAML: {e}")

        if not isinstance(data, dict) or "language" not in data:
            raise SpecificationError("Missing 'language' root key")

        return RobotLanguage(data)