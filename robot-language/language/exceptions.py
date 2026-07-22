
"""
Language Layer Exceptions.
"""


class LanguageError(Exception):
    """Base exception for language layer."""
    pass


class SpecificationError(LanguageError):
    """Raised when specification is invalid or cannot be loaded."""
    pass


class ValidationError(LanguageError):
    """Raised when validation fails."""
    pass


class DuplicateError(ValidationError):
    """Raised when duplicate definitions are found."""
    pass


class QueryError(LanguageError):
    """Raised when query operation fails."""
    pass