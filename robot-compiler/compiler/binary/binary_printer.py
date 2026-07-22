"""
Pretty printer for binary images.
"""

import binascii
from typing import List, Union

from .header import BinaryHeader
from .operand_encoder import OperandEncoder
from .instruction_encoder import InstructionEncoder
from .registry import RobotOpcodeRegistry


class BinaryPrinter:
    """Print a binary image in human-readable format (hex dump + disassembly)."""

    @staticmethod
    def print(binary: bytes, width: int = 16) -> str:
        """
        Return a hex dump of the binary.
        Example:
        0000: 52 42 49 4E 01 01 01 ...
        """
        lines = []
        for i in range(0, len(binary), width):
            chunk = binary[i:i+width]
            hex_part = ' '.join(f'{b:02X}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f"{i:04X}: {hex_part:<{width*3}} {ascii_part}")
        return '\n'.join(lines)

    @staticmethod
    def print_with_header(binary: bytes) -> str:
        """Print header info and hex dump."""
        try:
            header = BinaryHeader.from_bytes(binary)
            output = f"Magic: {header.magic:#010x}\n"
            output += f"ABI Version: {header.abi_version}\n"
            output += f"Endianness: {header.endianness.name}\n"
            output += f"Instruction Set Version: {header.instruction_set_version}\n"
            output += f"Program Size: {header.program_size}\n"
            output += f"Flags: {header.flags}\n"
            output += f"Checksum: {header.checksum}\n"
            output += "\nHex Dump:\n"
            output += BinaryPrinter.print(binary)
            return output
        except Exception:
            return BinaryPrinter.print(binary)