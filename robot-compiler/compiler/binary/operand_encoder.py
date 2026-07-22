import struct
from typing import Tuple
from ..isa import ISAOperand, OperandKind
from .layout import (
    OPERAND_TYPE_INTEGER,
    OPERAND_TYPE_FLOAT,
    OPERAND_TYPE_BOOLEAN,
    OPERAND_TYPE_STRING,
    OPERAND_TYPE_ENUM,
    OPERAND_TYPE_REGISTER,
    OPERAND_TYPE_LABEL,
    OPERAND_TYPE_CONSTANT_POOL,
)

# Ánh xạ OperandKind -> mã số
KIND_TO_TAG = {
    OperandKind.INTEGER: OPERAND_TYPE_INTEGER,
    OperandKind.FLOAT: OPERAND_TYPE_FLOAT,
    OperandKind.BOOLEAN: OPERAND_TYPE_BOOLEAN,
    OperandKind.STRING: OPERAND_TYPE_STRING,
    OperandKind.ENUM: OPERAND_TYPE_ENUM,
    OperandKind.REGISTER: OPERAND_TYPE_REGISTER,
    OperandKind.LABEL: OPERAND_TYPE_LABEL,
    OperandKind.CONSTANT_POOL: OPERAND_TYPE_CONSTANT_POOL,
}
TAG_TO_KIND = {v: k for k, v in KIND_TO_TAG.items()}


class OperandEncoder:
    @staticmethod
    def encode(operand: ISAOperand) -> bytes:
        kind = operand.kind
        value = operand.value

        tag = KIND_TO_TAG.get(kind)
        if tag is None:
            raise ValueError(f"Unknown operand kind: {kind}")

        result = struct.pack("<B", tag)

        if kind == OperandKind.INTEGER:
            result += struct.pack("<i", value)
        elif kind == OperandKind.FLOAT:
            result += struct.pack("<f", value)
        elif kind == OperandKind.BOOLEAN:
            result += struct.pack("<B", 1 if value else 0)
        elif kind == OperandKind.STRING:
            encoded = value.encode('utf-8')
            result += struct.pack("<I", len(encoded))
            result += encoded
        elif kind in (OperandKind.ENUM, OperandKind.REGISTER,
                      OperandKind.LABEL, OperandKind.CONSTANT_POOL):
            result += struct.pack("<I", value)
        else:
            raise ValueError(f"Unknown operand kind: {kind}")

        return result

    @staticmethod
    def decode(data: bytes, offset: int = 0) -> Tuple[ISAOperand, int]:
        tag = data[offset]
        offset += 1

        kind = TAG_TO_KIND.get(tag)
        if kind is None:
            raise ValueError(f"Unknown operand type tag: {tag}")

        if kind == OperandKind.INTEGER:
            val = struct.unpack("<i", data[offset:offset+4])[0]
            offset += 4
            return ISAOperand.integer(val), offset
        elif kind == OperandKind.FLOAT:
            val = struct.unpack("<f", data[offset:offset+4])[0]
            offset += 4
            return ISAOperand.float(val), offset
        elif kind == OperandKind.BOOLEAN:
            val = struct.unpack("<B", data[offset:offset+1])[0]
            offset += 1
            return ISAOperand.boolean(bool(val)), offset
        elif kind == OperandKind.STRING:
            length = struct.unpack("<I", data[offset:offset+4])[0]
            offset += 4
            val = data[offset:offset+length].decode('utf-8')
            offset += length
            return ISAOperand.string(val), offset
        elif kind in (OperandKind.ENUM, OperandKind.REGISTER,
                      OperandKind.LABEL, OperandKind.CONSTANT_POOL):
            val = struct.unpack("<I", data[offset:offset+4])[0]
            offset += 4
            if kind == OperandKind.ENUM:
                return ISAOperand.enum(val), offset
            elif kind == OperandKind.REGISTER:
                return ISAOperand.register(val), offset
            elif kind == OperandKind.LABEL:
                return ISAOperand.label(val), offset
            else:  # CONSTANT_POOL
                return ISAOperand.constant_pool(val), offset
        else:
            raise ValueError(f"Unknown operand kind during decode: {kind}")