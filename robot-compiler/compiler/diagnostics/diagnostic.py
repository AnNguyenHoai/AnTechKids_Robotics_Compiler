from enum import Enum
from typing import Optional
from ..ir.source_location import SourceLocation


class Severity(Enum):
    NOTE = "note"
    WARNING = "warning"
    ERROR = "error"


class Diagnostic:
    def __init__(
        self,
        severity: Severity,
        message: str,
        location: Optional[SourceLocation] = None,
        hint: Optional[str] = None,
    ):
        self.severity = severity
        self.message = message
        self.location = location
        self.hint = hint

    def __str__(self) -> str:
        prefix = self.severity.value.upper()
        loc = f"{self.location}: " if self.location else ""
        msg = f"{loc}{prefix}: {self.message}"
        if self.hint:
            msg += f"\n  hint: {self.hint}"
        return msg