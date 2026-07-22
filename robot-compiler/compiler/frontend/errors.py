from ..ir.source_location import SourceLocation
from typing import Optional


class CompilerError(Exception):
    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        self.message = message
        self.location = location
        super().__init__(self._format())

    def _format(self) -> str:
        if self.location:
            return f"{self.location}: error: {self.message}"
        return f"error: {self.message}"