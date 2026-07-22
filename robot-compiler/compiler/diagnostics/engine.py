from typing import List, Optional
from .diagnostic import Diagnostic, Severity


class DiagnosticEngine:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def emit(self, diagnostic: Diagnostic) -> None:
        self.diagnostics.append(diagnostic)

    def error(self, message: str, location=None, hint: Optional[str] = None) -> None:
        self.emit(Diagnostic(Severity.ERROR, message, location, hint))

    def warning(self, message: str, location=None, hint: Optional[str] = None) -> None:
        self.emit(Diagnostic(Severity.WARNING, message, location, hint))

    def note(self, message: str, location=None) -> None:
        self.emit(Diagnostic(Severity.NOTE, message, location))

    def has_errors(self) -> bool:
        return any(d.severity == Severity.ERROR for d in self.diagnostics)

    def get_errors(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.ERROR]

    def print_all(self) -> None:
        for d in self.diagnostics:
            print(d)