# compiler/isa/printer.py
from typing import TextIO, Optional
from .program import ISAProgram
from .function import ISAFunction
from .instruction import ISAInstruction
from .operand import ISAOperand, OperandKind
from compiler.generated.opcode import Opcode

class InstructionPrinter:
    """Human-readable printer for Robot ISA programs."""

    @classmethod
    def print(cls, program: ISAProgram, output: Optional[TextIO] = None) -> None:
        if output is None:
            import sys
            output = sys.stdout

        output.write(f"ISAProgram (functions: {program.function_count})\n\n")
        for func in program.functions:
            cls._print_function(func, output)

    @classmethod
    def _print_function(cls, func: ISAFunction, output: TextIO) -> None:
        output.write(f"Function: {func.name}")
        if func.entry_label:
            output.write(f" (entry: {func.entry_label})")
        output.write("\n")
        if func.metadata:
            output.write("  metadata:\n")
            for key, value in func.metadata.items():
                output.write(f"    {key}: {value}\n")

        for idx, ins in enumerate(func.instructions):
            output.write(f"  #{idx:04d} {cls._instruction_str(ins)}\n")
        output.write("\n")

    @classmethod
    def _instruction_str(cls, ins: ISAInstruction) -> str:
        parts = [ins.opcode.name]
        for op in ins.operands:
            parts.append(cls._operand_str(op))
        return " ".join(parts)

    @classmethod
    def _operand_str(cls, op: ISAOperand) -> str:
        kind = op.kind
        value = op.value
        if kind == OperandKind.INTEGER:
            return str(value)
        elif kind == OperandKind.FLOAT:
            return f"{value:.2f}"
        elif kind == OperandKind.BOOLEAN:
            return "true" if value else "false"
        elif kind == OperandKind.STRING:
            return f'"{value}"'
        elif kind == OperandKind.ENUM:
            return f"enum({value})"
        elif kind == OperandKind.REGISTER:
            return f"r{value}"
        elif kind == OperandKind.LABEL:
            return f"L{value}"
        elif kind == OperandKind.CONSTANT_POOL:
            return f"cp{value}"
        return str(value)