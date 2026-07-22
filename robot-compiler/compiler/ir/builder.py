from __future__ import annotations
from typing import List, Optional
from .program import IRProgram
from .function import IRFunction
from .basic_block import IRBasicBlock
from .instruction import IRInstruction
from .value import IRValue, ValueKind
from .opcode import IROpcode
from .source_location import SourceLocation


class IRBuilder:
    def __init__(self):
        self.program = IRProgram()
        self._current_function: Optional[IRFunction] = None
        self._current_block: Optional[IRBasicBlock] = None
        self._temp_counter = 0

    # ----- Program -----
    def create_program(self) -> IRProgram:
        self.program = IRProgram()
        return self.program

    def get_program(self) -> IRProgram:
        return self.program

    # ----- Function -----
    def create_function(self, name: str,
                        arguments: Optional[List[IRValue]] = None) -> IRFunction:
        func = IRFunction(name, arguments)
        self.program.add_function(func)
        self._current_function = func
        self._current_block = None
        return func

    def set_current_function(self, func: IRFunction) -> None:
        self._current_function = func

    def current_function(self) -> Optional[IRFunction]:
        return self._current_function

    # ----- Block -----
    def create_block(self, label: Optional[str] = None) -> IRBasicBlock:
        block = IRBasicBlock(label)
        if self._current_function is not None:
            self._current_function.add_block(block)
        self._current_block = block
        return block

    def set_current_block(self, block: IRBasicBlock) -> None:
        self._current_block = block

    def current_block(self) -> Optional[IRBasicBlock]:
        return self._current_block

    # ----- General append -----
    def append_instruction(self, opcode: IROpcode,
                           operands: Optional[List[IRValue]] = None,
                           location: Optional[SourceLocation] = None) -> IRInstruction:
        if self._current_block is None:
            raise RuntimeError("No current basic block. Call create_block() first.")
        ins = IRInstruction(opcode, operands, location)
        self._current_block.append(ins)
        return ins

    # ----- High-level APIs for RoboSim -----
    def move_run(self, direction: IRValue, speed: IRValue,
                 location: Optional[SourceLocation] = None) -> IRInstruction:
        return self.append_instruction(IROpcode.MOVE_RUN, [direction, speed], location)

    def move_run_time(self, direction: IRValue, speed: IRValue, duration: IRValue,
                      location: Optional[SourceLocation] = None) -> IRInstruction:
        return self.append_instruction(IROpcode.MOVE_RUN_TIME, [direction, speed, duration], location)

    def move_stop(self, location: Optional[SourceLocation] = None) -> IRInstruction:
        return self.append_instruction(IROpcode.MOVE_STOP, [], location)

    def wait(self, duration: IRValue,
             location: Optional[SourceLocation] = None) -> IRInstruction:
        return self.append_instruction(IROpcode.WAIT, [duration], location)

    def call(self, func_name: IRValue,
             location: Optional[SourceLocation] = None) -> IRInstruction:
        return self.append_instruction(IROpcode.CALL, [func_name], location)

    def jump(self, target: IRValue,
             location: Optional[SourceLocation] = None) -> IRInstruction:
        return self.append_instruction(IROpcode.JUMP, [target], location)

    def jump_if_false(self, cond: IRValue, target: IRValue,
                      location: Optional[SourceLocation] = None) -> IRInstruction:
        return self.append_instruction(IROpcode.JUMP_IF_FALSE, [cond, target], location)

    # ----- Values -----
    def const_int(self, val: int) -> IRValue:
        return IRValue.integer(val)

    def const_float(self, val: float) -> IRValue:
        return IRValue.float(val)

    def const_bool(self, val: bool) -> IRValue:
        return IRValue.boolean(val)

    def const_string(self, val: str) -> IRValue:
        return IRValue.string(val)

    def var(self, name: str, index: Optional[int] = None) -> IRValue:
        return IRValue.variable(name, index)

    def temp(self, name: Optional[str] = None) -> IRValue:
        self._temp_counter += 1
        idx = self._temp_counter
        if name is None:
            name = f"t{idx}"
        return IRValue.temporary(name, idx)