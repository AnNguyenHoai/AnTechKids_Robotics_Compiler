from __future__ import annotations
from typing import TextIO
from .program import IRProgram
from .function import IRFunction
from .basic_block import IRBasicBlock
from .instruction import IRInstruction
from .value import IRValue, ValueKind
from .opcode import IROpcode
from .source_location import SourceLocation


class IRPrinter:
    @classmethod
    def print(cls, program: IRProgram, output: TextIO = None) -> None:
        if output is None:
            import sys
            output = sys.stdout

        output.write("IRProgram\n")
        output.write(f"  functions: {len(program.functions)}\n")
        output.write(f"  globals: {len(program.globals)}\n\n")

        if program.metadata:
            output.write("  metadata:\n")
            for key, value in program.metadata.items():
                output.write(f"    {key}: {value}\n")
            output.write("\n")

        for func in program.functions:
            cls._print_function(func, output)

    @classmethod
    def _print_function(cls, func: IRFunction, output: TextIO) -> None:
        output.write(f"Function: {func.name}\n")
        if func.arguments:
            output.write("  arguments:\n")
            for arg in func.arguments:
                output.write(f"    {cls._value_str(arg)}\n")
        if func.metadata:
            output.write("  metadata:\n")
            for key, value in func.metadata.items():
                output.write(f"    {key}: {value}\n")

        # Track instruction index within function
        ins_index = 0
        for block in func.blocks:
            cls._print_block(block, output, ins_index)
            ins_index += block.size()

        output.write("\n")

    @classmethod
    def _print_block(cls, block: IRBasicBlock, output: TextIO, start_index: int) -> None:
        label = block.label if block.label else "(unnamed)"
        output.write(f"  Block {label}:\n")
        for i, ins in enumerate(block.instructions):
            idx = start_index + i
            output.write(f"    #{idx:04d} {cls._instruction_str(ins)}\n")
            # Source location
            if ins.location:
                output.write(f"      Source: {ins.location}\n")

    @classmethod
    def _instruction_str(cls, ins: IRInstruction) -> str:
        parts = [ins.opcode.name]
        for op in ins.operands:
            parts.append(cls._value_str(op))
        return " ".join(parts)

    @classmethod
    def _value_str(cls, value: IRValue) -> str:
        if value.name:
            return f"{value.kind.name.lower()}({value.name})"
        return f"{value.kind.name.lower()}({repr(value.value)})"