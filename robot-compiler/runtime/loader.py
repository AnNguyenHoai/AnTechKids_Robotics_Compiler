# runtime/loader.py
from typing import List
from compiler.binary import BinaryProgram
from compiler.isa import OperandKind
from compiler.generated.opcode import Opcode
from compiler.binary.instruction_encoder import InstructionEncoder
from .program import RuntimeProgram
from .function import RuntimeFunction
from .instruction import RuntimeInstruction
from .exceptions import (
    InvalidBinaryException,
    UnsupportedVersionException,
    InvalidInstructionException,
)

class ProgramLoader:
    @staticmethod
    def load(binary: BinaryProgram) -> RuntimeProgram:
        # Validate header
        header = binary.header
        if header.magic != 0x4E494252:
            raise InvalidBinaryException(...)
        if header.abi_version != 1:
            raise UnsupportedVersionException(...)

        constants = list(binary.constant_pool.constants)
        stream_data = binary.instruction_stream.data
        offset = 0
        all_instructions: List[RuntimeInstruction] = []
        function_list: List[RuntimeFunction] = []

        opcode_registry = {op.value: op for op in Opcode}

        for ft_entry in binary.function_table.entries:
            func_id = ft_entry.function_id
            start_offset = ft_entry.entry_offset
            count = ft_entry.instruction_count

            func_instructions: List[RuntimeInstruction] = []
            temp_offset = start_offset
            for _ in range(count):
                ins, temp_offset = InstructionEncoder.decode(
                    stream_data, temp_offset, opcode_registry
                )
                operands = []
                for op in ins.operands:
                    if op.kind == OperandKind.INTEGER:
                        operands.append(op.as_integer())
                    elif op.kind == OperandKind.FLOAT:
                        operands.append(op.as_float())
                    elif op.kind == OperandKind.BOOLEAN:
                        operands.append(op.as_boolean())
                    elif op.kind == OperandKind.STRING:
                        operands.append(op.as_string())
                    elif op.kind in (OperandKind.ENUM, OperandKind.REGISTER, OperandKind.LABEL, OperandKind.CONSTANT_POOL):
                        operands.append(op.as_index())
                    else:
                        raise InvalidInstructionException(f"Unsupported operand kind: {op.kind}")

                runtime_ins = RuntimeInstruction(
                    opcode=ins.opcode,  # ins.opcode là Opcode
                    operands=operands,
                    index=len(all_instructions)
                )
                all_instructions.append(runtime_ins)
                func_instructions.append(runtime_ins)

            func = RuntimeFunction(
                function_id=func_id,
                entry_index=len(all_instructions) - count,
                instruction_count=count,
                instructions=func_instructions,
            )
            function_list.append(func)

        entry_id = 0 if function_list else -1
        return RuntimeProgram(
            constants=constants,
            functions=function_list,
            instructions=all_instructions,
            entry_function_id=entry_id,
            abi_version=header.abi_version,
        )