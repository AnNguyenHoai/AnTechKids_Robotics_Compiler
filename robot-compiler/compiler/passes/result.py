from typing import List, Optional
from ..diagnostics.diagnostic import Diagnostic


class PassResult:
    """Result of executing a compiler pass."""

    def __init__(self, success: bool = True, diagnostics: Optional[List[Diagnostic]] = None):
        self.success = success
        self.diagnostics = diagnostics or []

    @classmethod
    def ok(cls) -> "PassResult":
        return cls(True)

    @classmethod
    def error(cls, diagnostic: Diagnostic) -> "PassResult":
        return cls(False, [diagnostic])

    @classmethod
    def errors(cls, diagnostics: List[Diagnostic]) -> "PassResult":
        return cls(False, diagnostics)

    def merge(self, other: "PassResult") -> "PassResult":
        return PassResult(
            success=self.success and other.success,
            diagnostics=self.diagnostics + other.diagnostics
        )