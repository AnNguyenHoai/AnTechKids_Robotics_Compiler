from typing import Optional
from ..ir import IRProgram
from ..diagnostics.engine import DiagnosticEngine


class PassContext:
    """Context shared between passes during compilation."""

    def __init__(self, program: IRProgram, diagnostics: Optional[DiagnosticEngine] = None):
        self.program = program
        self.diagnostics = diagnostics or DiagnosticEngine()
        self.config = {}  # For future configuration