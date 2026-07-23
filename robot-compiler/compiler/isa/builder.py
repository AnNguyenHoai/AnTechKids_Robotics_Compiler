# compiler/isa/builder.py
from typing import Optional, List
from compiler.generated.opcode import Opcode
from .operand import ISAOperand, OperandKind
from .instruction import ISAInstruction
from .function import ISAFunction
from .program import ISAProgram

class InstructionBuilder:
    """Builder for creating valid Robot ISA instructions."""

    def __init__(self):
        self._program = ISAProgram()
        self._current_function: Optional[ISAFunction] = None
        self._label_counter = 0

    # ----- Program -----
    def create_program(self, metadata: Optional[dict] = None) -> ISAProgram:
        self._program = ISAProgram(metadata)
        return self._program

    def get_program(self) -> ISAProgram:
        return self._program

    # ----- Function -----
    def create_function(self, name: str, entry_label: Optional[str] = None) -> ISAFunction:
        func = ISAFunction(name, entry_label)
        self._program.add_function(func)
        self._current_function = func
        return func

    def set_current_function(self, func: ISAFunction) -> None:
        self._current_function = func

    def current_function(self) -> Optional[ISAFunction]:
        return self._current_function

    # ----- Instruction creation -----
    def emit(self, opcode: Opcode, operands: Optional[List[ISAOperand]] = None) -> ISAInstruction:
        """Public method to emit any instruction."""
        if self._current_function is None:
            raise RuntimeError("No current function. Call create_function() first.")
        ins = ISAInstruction(opcode, operands)
        self._current_function.add_instruction(ins)
        return ins

    def _emit(self, opcode: Opcode, operands: Optional[List[ISAOperand]] = None) -> ISAInstruction:
        """Internal method (kept for compatibility)."""
        return self.emit(opcode, operands)

    # ----- Movement (deprecated, use emit directly) -----
    def move_run(self, direction: ISAOperand, speed: ISAOperand) -> ISAInstruction:
        return self.emit(Opcode.FORWARD, [speed])  # Temporary fallback

    def move_run_time(self, direction: ISAOperand, speed: ISAOperand,
                      duration: ISAOperand) -> ISAInstruction:
        return self.emit(Opcode.WAIT, [duration])

    def move_stop(self) -> ISAInstruction:
        return self.emit(Opcode.STOP, [])

    # ----- Timing -----
    def wait(self, duration: ISAOperand) -> ISAInstruction:
        return self.emit(Opcode.WAIT, [duration])

    # ----- Control flow -----
    def jump(self, target: ISAOperand) -> ISAInstruction:
        return self.emit(Opcode.JUMP, [target])

    def jump_if(self, condition: ISAOperand, target: ISAOperand) -> ISAInstruction:
        return self.emit(Opcode.JUMP_IF, [condition, target])

    # ----- Function -----
    def call(self, func_name: ISAOperand) -> ISAInstruction:
        return self.emit(Opcode.CALL, [func_name])

    def return_(self) -> ISAInstruction:
        return self.emit(Opcode.RETURN, [])

    # ----- Helper -----
    def new_label(self) -> ISAOperand:
        self._label_counter += 1
        return ISAOperand.label(self._label_counter)

    def resolve_label(self, label: ISAOperand, index: int) -> None:
        """Record label position."""
        if self._current_function:
            label_name = f"L{label.as_index()}"
            self._current_function.add_label(label_name, index)

    def const_int(self, val: int) -> ISAOperand:
        return ISAOperand.integer(val)

    def const_float(self, val: float) -> ISAOperand:
        return ISAOperand.float(val)

    def const_string(self, val: str) -> ISAOperand:
        return ISAOperand.string(val)

    def const_bool(self, val: bool) -> ISAOperand:
        return ISAOperand.boolean(val)

    def register(self, idx: int) -> ISAOperand:
        return ISAOperand.register(idx)

    def label(self, idx: int) -> ISAOperand:
        return ISAOperand.label(idx)

    def constant_pool(self, idx: int) -> ISAOperand:
        return ISAOperand.constant_pool(idx)