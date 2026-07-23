"""
Backend Lowering: Platform IR → Robot ISA
"""

from typing import Optional, Dict, Any
from ..ir import IRProgram, IRFunction, IRBasicBlock, IRInstruction, IROpcode, IRValue, ValueKind
from ..passes import CompilerPass, PassContext, PassResult
from .program import ISAProgram
from .function import ISAFunction
from .builder import InstructionBuilder
from .printer import InstructionPrinter
from .operand import ISAOperand, OperandKind
from compiler.generated.opcode import Opcode


class BackendLowering(CompilerPass):
    """Lower Platform IR to Robot ISA."""

    name = "Backend Lowering"

    def __init__(self, target_function: Optional[str] = None):
        self.target_function = target_function or "main"

    def run(self, context: PassContext) -> PassResult:
        ir_program = context.program
        isa_program = self.lower(ir_program)
        context.config["isa_program"] = isa_program
        return PassResult.ok()

    def lower(self, ir_program: IRProgram) -> ISAProgram:
        builder = InstructionBuilder()
        builder.create_program()

        target_ir_func = None
        for func in ir_program.functions:
            if func.name == self.target_function:
                target_ir_func = func
                break

        if target_ir_func is None and ir_program.functions:
            target_ir_func = ir_program.functions[0]

        if target_ir_func is None:
            return builder.get_program()

        isa_func = builder.create_function(target_ir_func.name)
        self._lower_function(target_ir_func, isa_func, builder)
        return builder.get_program()

    def _lower_function(self, ir_func: IRFunction, isa_func: ISAFunction,
                        builder: InstructionBuilder) -> None:
        for block in ir_func.blocks:
            label_op = builder.new_label()
            builder.resolve_label(label_op, isa_func.size)

            for ins in block.instructions:
                self._lower_instruction(ins, builder)

    def _lower_instruction(self, ir_ins: IRInstruction, builder: InstructionBuilder) -> None:
        opcode = ir_ins.opcode
        operands = ir_ins.operands

        if opcode == IROpcode.MOVE_RUN:
            if len(operands) >= 2:
                dir_op = self._lower_value(operands[0])
                speed_op = self._lower_value(operands[1])
                dir_str = dir_op.as_string().lower()
                if dir_str == "forward":
                    builder.emit(Opcode.Forward, [speed_op])
                elif dir_str == "backward":
                    builder.emit(Opcode.Backward, [speed_op])
                elif dir_str == "left":
                    builder.emit(Opcode.TurnLeft, [speed_op])
                elif dir_str == "right":
                    builder.emit(Opcode.TurnRight, [speed_op])
                else:
                    raise ValueError(f"Invalid direction: {dir_str}")

        elif opcode == IROpcode.MOVE_RUN_TIME:
            if len(operands) >= 3:
                dir_op = self._lower_value(operands[0])
                speed_op = self._lower_value(operands[1])
                dur_op = self._lower_value(operands[2])
                # For simplicity, just emit WAIT with duration
                builder.emit(Opcode.Wait, [dur_op])

        elif opcode == IROpcode.MOVE_STOP:
            builder.emit(Opcode.Stop, [])

        elif opcode == IROpcode.WAIT:
            if operands:
                dur_op = self._lower_value(operands[0])
                builder.emit(Opcode.Wait, [dur_op])

        elif opcode == IROpcode.CALL:
            if operands:
                target_op = self._lower_value(operands[0])
                builder.emit(Opcode.Call, [target_op])

        elif opcode == IROpcode.RETURN:
            builder.emit(Opcode.Return, [])

        elif opcode == IROpcode.JUMP:
            if operands:
                target_op = self._lower_value(operands[0])
                builder.emit(Opcode.Jump, [target_op])

        elif opcode in (IROpcode.JUMP_IF_FALSE, IROpcode.JUMP_IF_TRUE):
            if len(operands) >= 2:
                cond_op = self._lower_value(operands[0])
                target_op = self._lower_value(operands[1])
                builder.emit(Opcode.JumpIfFalse if opcode == IROpcode.JUMP_IF_FALSE else Opcode.JumpIfTrue,
                             [cond_op, target_op])

    def _lower_value(self, ir_value: IRValue) -> ISAOperand:
        kind = ir_value.kind
        value = ir_value.value

        if kind == ValueKind.INTEGER:
            return ISAOperand.integer(value)
        elif kind == ValueKind.FLOAT:
            return ISAOperand.float(value)
        elif kind == ValueKind.BOOLEAN:
            return ISAOperand.boolean(value)
        elif kind == ValueKind.STRING:
            return ISAOperand.string(value)
        elif kind in (ValueKind.VARIABLE, ValueKind.TEMPORARY):
            return ISAOperand.register(value)
        elif kind == ValueKind.ENUM:
            return ISAOperand.enum(value)
        else:
            return ISAOperand.integer(value if isinstance(value, int) else 0)