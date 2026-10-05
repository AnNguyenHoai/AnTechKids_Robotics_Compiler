import ast
import inspect


class CompilerError(Exception):

    def __init__(self, message, *, code="E_COMPILE", severity="error", context=None):
        self.code = code
        self.severity = severity
        self.context = dict(context or {})
        self._capture_ast_context()
        self._add_hint(message)
        super().__init__(message)

    def _capture_ast_context(self):
        """Best-effort source location for legacy compiler raises.

        Compiler handlers historically raise CompilerError directly. Capturing the
        nearest AST local here adds diagnostics without changing compiler behavior
        or every existing raise site.
        """
        if "line" in self.context:
            return
        frame = inspect.currentframe()
        try:
            frame = frame.f_back if frame is not None else None
            while frame is not None:
                if frame.f_code.co_filename.endswith("error.py"):
                    frame = frame.f_back
                    continue
                node = None
                for key in ("node", "expr", "arg", "target", "value"):
                    candidate = frame.f_locals.get(key)
                    if isinstance(candidate, ast.AST) and hasattr(candidate, "lineno"):
                        node = candidate
                        break
                if node is not None:
                    self.context.setdefault("line", getattr(node, "lineno", None))
                    self.context.setdefault("column", getattr(node, "col_offset", 0) + 1)
                    self.context.setdefault("end_line", getattr(node, "end_lineno", None))
                    end_col = getattr(node, "end_col_offset", None)
                    if end_col is not None:
                        self.context.setdefault("end_column", end_col + 1)
                    self.context.setdefault("syntax_node", type(node).__name__)
                    break
                frame = frame.f_back
        finally:
            del frame

    def _add_hint(self, message):
        if "hint" in self.context:
            return
        text = str(message)
        hint = None
        if "is not defined" in text:
            hint = "Define the variable before it is used, or declare it global inside the function when it refers to module state."
        elif "Unsupported syntax node" in text or "Unsupported expression type" in text:
            hint = "Rewrite this statement using syntax supported by the RoboSim language subset."
        elif "expects exactly" in text:
            hint = "Check the number of inputs connected to this Robot API or function call."
        elif "Unknown function or Robot API" in text:
            hint = "Check the function name and use a Robot API supported by the selected target."
        elif "does not return a value" in text:
            hint = "Use this Robot API as a statement instead of assigning or comparing its result."
        if hint:
            self.context["hint"] = hint

    def to_diagnostic(self):
        return {
            "code": self.code,
            "severity": self.severity,
            "message": str(self),
            "context": {key: value for key, value in self.context.items() if value is not None},
        }


def syntax_error_diagnostic(exc):
    """Normalize Python parser failures to the compiler diagnostic contract."""
    context = {
        "line": exc.lineno,
        "column": exc.offset,
        "end_line": getattr(exc, "end_lineno", None),
        "end_column": getattr(exc, "end_offset", None),
        "source": exc.text.rstrip("\r\n") if exc.text else None,
        "hint": "Check the highlighted line for incomplete or invalid Python syntax.",
    }
    return {
        "code": "INVALID_SOURCE",
        "severity": "error",
        "message": exc.msg,
        "context": {key: value for key, value in context.items() if value is not None},
    }
