import struct
from ..isa import ISAProgram, OperandKind

class ConstantPoolEncoder:
    @staticmethod
    def encode(program: ISAProgram) -> bytes:
        constants = []
        for func in program.functions:
            for ins in func.instructions:
                for op in ins.operands:
                    if op.kind == OperandKind.STRING:
                        constants.append(op.as_string())
        unique = list(dict.fromkeys(constants))

        result = struct.pack("<I", len(unique))
        for s in unique:
            encoded = s.encode('utf-8')
            result += struct.pack("<I", len(encoded))
            result += encoded
        return result

    @staticmethod
    def decode(data: bytes, offset: int = 0):
        """Decode constant pool from binary data."""
        count = struct.unpack("<I", data[offset:offset+4])[0]
        offset += 4
        strings = []
        for _ in range(count):
            length = struct.unpack("<I", data[offset:offset+4])[0]
            offset += 4
            s = data[offset:offset+length].decode('utf-8')
            offset += length
            strings.append(s)
        return strings, offset