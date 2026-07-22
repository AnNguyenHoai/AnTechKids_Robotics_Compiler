"""
Binary Layout Specification for Robot ISA.

This module documents the binary layout constants.
The actual encoding is done by the encoders.
"""

# Magic number: "RBIN" in ASCII (0x52 0x42 0x49 0x4E)
MAGIC = 0x4E494252  # Little-endian bytes: 'R','B','I','N'

# ABI Version
ABI_VERSION = 1

# Instruction Set Version
INSTRUCTION_SET_VERSION = 1

# Header size in bytes
HEADER_SIZE = 32  # bytes

# Max instruction size (opcode + operands)
MAX_INSTRUCTION_SIZE = 16  # bytes

# Operand type tags (for variable-length encoding)
OPERAND_TYPE_INTEGER = 0x01
OPERAND_TYPE_FLOAT = 0x02
OPERAND_TYPE_BOOLEAN = 0x03
OPERAND_TYPE_STRING = 0x04
OPERAND_TYPE_ENUM = 0x05
OPERAND_TYPE_REGISTER = 0x06
OPERAND_TYPE_LABEL = 0x07
OPERAND_TYPE_CONSTANT_POOL = 0x08