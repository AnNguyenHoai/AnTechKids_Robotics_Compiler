from typing import List, Optional
from .base import CompilerPass
from .context import PassContext
from .result import PassResult


class PassManager:
    """Manages registration and execution of compiler passes."""

    def __init__(self):
        self.passes: List[CompilerPass] = []

    def register(self, pass_: CompilerPass) -> None:
        self.passes.append(pass_)

    def run(self, context: PassContext) -> PassResult:
        final_result = PassResult.ok()
        for pass_ in self.passes:
            result = pass_.run(context)
            if not result.success:
                # Stop on first error (can be changed later)
                final_result = final_result.merge(result)
                break
            final_result = final_result.merge(result)
        return final_result