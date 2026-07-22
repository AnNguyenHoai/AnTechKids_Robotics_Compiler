# robot-compiler/runtime/iterator.py
from typing import Optional, List
from .program import RuntimeProgram
from .instruction import RuntimeInstruction


class InstructionIterator:
    """
    Iterator over instructions of a specific function or the entire program.
    Provides the single interface for instruction access by the VM.
    """
    def __init__(self, program: RuntimeProgram, function_id: Optional[int] = None):
        self._program = program
        self._function_id = function_id
        self._instructions: List[RuntimeInstruction] = []
        self._current_index: int = 0

        if function_id is not None:
            func = program.get_function(function_id)
            if func is None:
                raise ValueError(f"Function {function_id} not found")
            self._instructions = func.instructions
        else:
            self._instructions = program.instructions

    def current(self) -> Optional[RuntimeInstruction]:
        if 0 <= self._current_index < len(self._instructions):
            return self._instructions[self._current_index]
        return None

    def next(self) -> Optional[RuntimeInstruction]:
        ins = self.current()
        if ins is not None:
            self._current_index += 1
        return ins

    def jump(self, index: int) -> None:
        if index < 0 or index >= len(self._instructions):
            raise ValueError(f"Invalid jump target: {index}")
        self._current_index = index

    def seek(self, index: int) -> None:
        self._current_index = index

    def has_next(self) -> bool:
        return self._current_index < len(self._instructions)

    def peek(self, offset: int = 0) -> Optional[RuntimeInstruction]:
        idx = self._current_index + offset
        if 0 <= idx < len(self._instructions):
            return self._instructions[idx]
        return None

    def reset(self) -> None:
        self._current_index = 0