class CompilerError(Exception):

    def __init__(self, message, *, code="E_COMPILE", severity="error", context=None):
        self.code = code
        self.severity = severity
        self.context = dict(context or {})
        super().__init__(message)

    def to_diagnostic(self):
        return {
            "code": self.code,
            "severity": self.severity,
            "message": str(self),
            "context": dict(self.context),
        }
