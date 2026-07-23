# compiler/binary/instruction_encoder.py
import struct
from typing import Tuple, Dict
from ..isa import ISAInstruction, ISAOperand
from .operand_encoder import OperandEncoder
from ..generated.opcode import Opcode  # dùng trực tiếp Opcode

class InstructionEncoder:
    @staticmethod
    def encode(instruction: ISAInstruction) -> bytes:
        result = struct.pack("<B", instruction.opcode.value)  # opcode là IntEnum
        result += struct.pack("<B", instruction.operand_count)
        for op in instruction.operands:
            result += OperandEncoder.encode(op)
        return result

    @staticmethod
    def decode(data: bytes, offset: int, registry: Dict[int, Opcode]) -> Tuple[ISAInstruction, int]:
        opcode_val = data[offset]
        offset += 1
        opcode = registry.get(opcode_val)
        if opcode is None:
            raise ValueError(f"Unknown opcode value: {opcode_val}")
        operand_count = data[offset]
        offset += 1
        operands = []
        for _ in range(operand_count):
            op, offset = OperandEncoder.decode(data, offset)
            operands.append(op)
        return ISAInstruction(opcode, operands), offset