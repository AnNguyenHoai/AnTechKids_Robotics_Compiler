# robot-compiler/runtime/exceptions.py
class RuntimeError(Exception):
    """Base class for runtime errors."""
    pass


class InvalidBinaryException(RuntimeError):
    """Raised when binary magic or structure is invalid."""
    pass


class UnsupportedVersionException(RuntimeError):
    """Raised when ABI version is not supported."""
    pass


class InvalidInstructionException(RuntimeError):
    """Raised when an instruction is malformed or unsupported."""
    pass


class InvalidConstantReferenceException(RuntimeError):
    """Raised when a constant pool reference is out of bounds."""
    pass


class InvalidFunctionReferenceException(RuntimeError):
    """Raised when a function table reference is invalid."""
    pass