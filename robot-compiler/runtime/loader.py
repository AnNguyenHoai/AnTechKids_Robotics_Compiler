# robot-compiler/runtime/loader.py
from typing import List
from ..compiler.binary import BinaryProgram
from ..compiler.isa import RobotOpcode, OperandKind
from ..compiler.binary.instruction_encoder import InstructionEncoder
from .program import RuntimeProgram
from .function import RuntimeFunction
from .instruction import RuntimeInstruction
from .exceptions import (
    InvalidBinaryException,
    UnsupportedVersionException,
    InvalidInstructionException,
)


class ProgramLoader:
    """
    Loads a BinaryProgram (from compiler) into a RuntimeProgram,
    performing validation, decoding, and resolution.
    """
    @staticmethod
    def load(binary: BinaryProgram) -> RuntimeProgram:
        # 1. Validate header
        header = binary.header
        if header.magic != 0x4E494252:
            raise InvalidBinaryException(
                f"Invalid magic number: {header.magic:#010x} (expected 0x4E494252)"
            )
        if header.abi_version != 1:
            raise UnsupportedVersionException(
                f"Unsupported ABI version: {header.abi_version} (only version 1 is supported)"
            )

        # 2. Build constant pool list
        constants = list(binary.constant_pool.constants)

        # 3. Decode instruction stream
        stream_data = binary.instruction_stream.data
        offset = 0
        all_instructions: List[RuntimeInstruction] = []
        function_list: List[RuntimeFunction] = []

        # Registry for opcode enum by numeric value
        opcode_registry = {op.value: op for op in RobotOpcode}

        # Iterate through function table entries
        for ft_entry in binary.function_table.entries:
            func_id = ft_entry.function_id
            start_offset = ft_entry.entry_offset
            count = ft_entry.instruction_count

            # Decode instructions for this function
            func_instructions: List[RuntimeInstruction] = []
            temp_offset = start_offset
            for idx in range(count):
                # Decode one ISAInstruction from raw bytes
                ins, temp_offset = InstructionEncoder.decode(
                    stream_data, temp_offset, opcode_registry
                )
                # Convert to RuntimeInstruction
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
                    elif op.kind in (
                        OperandKind.ENUM,
                        OperandKind.REGISTER,
                        OperandKind.LABEL,
                        OperandKind.CONSTANT_POOL,
                    ):
                        operands.append(op.as_index())
                    else:
                        raise InvalidInstructionException(
                            f"Unsupported operand kind: {op.kind}"
                        )

                runtime_ins = RuntimeInstruction(
                    opcode=ins.opcode,
                    operands=operands,
                    index=len(all_instructions)
                )
                all_instructions.append(runtime_ins)
                func_instructions.append(runtime_ins)

            # Create RuntimeFunction
            func = RuntimeFunction(
                function_id=func_id,
                entry_index=len(all_instructions) - count,
                instruction_count=count,
                instructions=func_instructions,
            )
            function_list.append(func)

        # 4. Build and return RuntimeProgram
        entry_id = 0 if function_list else -1
        return RuntimeProgram(
            constants=constants,
            functions=function_list,
            instructions=all_instructions,
            entry_function_id=entry_id,
            abi_version=header.abi_version,
        )