import ast
from pathlib import Path
from typing import Optional
from .errors import CompilerError


class Parser:
    @staticmethod
    def parse(source_path: Path) -> ast.AST:
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                source = f.read()
        except FileNotFoundError:
            raise CompilerError(f"Source file not found: {source_path}")

        try:
            tree = ast.parse(source, filename=str(source_path))
        except SyntaxError as e:
            raise CompilerError(f"Syntax error: {e}", None)  # location from e?
        return tree