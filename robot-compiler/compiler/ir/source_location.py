from dataclasses import dataclass
from typing import Optional


@dataclass
class SourceLocation:
    file: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"