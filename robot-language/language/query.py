"""
Language Query Service.

Provides read-only access to RobotLanguage model.
All generators and validators must use this interface instead of direct model access.
"""

from typing import Dict, List, Generator, Tuple, Optional, Any


class LanguageQuery:
    def __init__(self, language):
        self._language = language

    @property
    def name(self) -> str:
        return self._language.name

    @property
    def version(self) -> str:
        return self._language.version

    # ---------- Category ----------
    def categories(self) -> Dict:
        """Return all categories (raw dict)."""
        return self._language.categories

    def category(self, name: str) -> Optional[Dict]:
        """Return a specific category by name."""
        return self._language.categories.get(name)

    def category_count(self) -> int:
        """Number of categories."""
        return len(self._language.categories)

    def category_names(self) -> List[str]:
        """List of category names."""
        return list(self._language.categories.keys())

    # ---------- Function iteration ----------
    def functions(self) -> Generator[Tuple[str, Dict, Dict], None, None]:
        """
        Yield all functions with their category name and category data.
        Yields: (category_name, category, function)
        """
        for cat_name, cat in self._language.categories.items():
            for func in cat.get("functions", []):
                yield cat_name, cat, func

    def public_functions(self) -> Generator[Tuple[str, Dict, Dict], None, None]:
        """Yield only non‑internal functions."""
        for cat_name, cat, func in self.functions():
            if cat_name != "internal":
                yield cat_name, cat, func

    def internal_functions(self) -> Generator[Tuple[str, Dict, Dict], None, None]:
        """Yield only internal functions."""
        for cat_name, cat, func in self.functions():
            if cat_name == "internal":
                yield cat_name, cat, func

    def function(self, name: str) -> Optional[Dict]:
        """Return function dict by name."""
        for _, _, func in self.functions():
            if func["name"] == name:
                return func
        return None

    def function_names(self) -> List[str]:
        """List all function names."""
        return [f["name"] for _, _, f in self.functions()]

    def function_count(self) -> int:
        """Total number of functions."""
        return sum(1 for _ in self.functions())

    # ---------- Function properties ----------
    def category_of(self, func: Dict) -> str:
        """Return category name of a function."""
        for cat_name, _, f in self.functions():
            if f is func:  # identity comparison
                return cat_name
        # Fallback: search by name (less efficient, but safe)
        name = func.get("name")
        for cat_name, _, f in self.functions():
            if f.get("name") == name:
                return cat_name
        raise KeyError(f"Function {func.get('name')} not found")

    def module_of(self, category_name: str) -> Optional[str]:
        """Get module name for a category."""
        cat = self.category(category_name)
        return cat.get("module") if cat else None

    def module_of_func(self, func: Dict) -> str:
        """Get module name for the category of a function."""
        cat_name = self.category_of(func)
        return self.module_of(cat_name)

    def handler_of(self, category_name: str) -> Optional[str]:
        """Get handler class name for a category."""
        cat = self.category(category_name)
        return cat.get("handler") if cat else None

    def handler_of_func(self, func: Dict) -> str:
        """Get handler class name for the category of a function."""
        cat_name = self.category_of(func)
        return self.handler_of(cat_name)

    def opcode_of(self, func: Dict) -> str:
        """Return opcode string of a function."""
        return func["opcode"]

    def opcode_id_of(self, func: Dict) -> int:
        """Return opcode ID of a function."""
        return func["opcode_id"]

    def description_of(self, func: Dict) -> str:
        """Return description of a function."""
        return func.get("description", "")

    def arguments_of(self, func: Dict) -> List[Dict]:
        """Return list of argument dicts."""
        return func.get("args", [])

    def argument_count_of(self, func: Dict) -> int:
        """Return number of arguments."""
        return len(self.arguments_of(func))

    def is_internal(self, func: Dict) -> bool:
        """Check if a function belongs to internal category."""
        return self.category_of(func) == "internal"

    def is_public(self, func: Dict) -> bool:
        """Check if a function is public (non‑internal)."""
        return not self.is_internal(func)

    # ---------- Lists ----------
    def opcodes(self) -> List[str]:
        """Return list of all opcode names."""
        return [f["opcode"] for _, _, f in self.functions()]

    def opcode_ids(self) -> List[int]:
        """Return list of all opcode IDs."""
        return [f["opcode_id"] for _, _, f in self.functions()]

    def handlers(self) -> List[str]:
        """Return list of all handler class names."""
        return [cat["handler"] for cat in self._language.categories.values()]

    def modules(self) -> List[str]:
        """Return list of all module names (for handlers)."""
        return [cat["module"] for cat in self._language.categories.values()]

    # ---------- Statistics ----------
    def statistics(self) -> Dict[str, Any]:
        """Return build statistics."""
        return {
            "categories": self.category_count(),
            "functions": self.function_count(),
            "opcodes": len(self.opcodes()),
            "public_functions": sum(1 for _ in self.public_functions()),
            "internal_functions": sum(1 for _ in self.internal_functions()),
        }