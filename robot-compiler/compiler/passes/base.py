from abc import ABC, abstractmethod
from typing import Optional
from .context import PassContext
from .result import PassResult


class CompilerPass(ABC):
    """Base class for all compiler passes."""

    name: str = "UnnamedPass"

    @abstractmethod
    def run(self, context: PassContext) -> PassResult:
        """Execute the pass on the given context."""
        pass