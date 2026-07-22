"""
Binary Header – fixed-size header for Robot binary images.
"""

import struct
from dataclasses import dataclass
from enum import IntEnum


class Magic(IntEnum):
    ROBOT_BINARY = 0x4E494252  # little-endian bytes sẽ là "RBIN"


class Endianness(IntEnum):
    LITTLE = 0
    BIG = 1


@dataclass
class BinaryHeader:
    magic: int = Magic.ROBOT_BINARY
    abi_version: int = 1
    endianness: int = Endianness.LITTLE
    instruction_set_version: int = 1
    program_size: int = 0
    flags: int = 0
    checksum: int = 0

    @classmethod
    def default(cls) -> "BinaryHeader":
        return cls()

    def to_bytes(self) -> bytes:
        return struct.pack(
            "<IBBIBII",
            self.magic,
            self.abi_version,
            self.endianness,
            self.instruction_set_version,
            self.program_size,
            self.flags,
            self.checksum,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "BinaryHeader":
        magic, abi_ver, endian, iset_ver, prog_size, flags, checksum = struct.unpack(
            "<IBBIBII", data[:20]
        )
        return cls(magic, abi_ver, endian, iset_ver, prog_size, flags, checksum)

    def size(self) -> int:
        return 19  # thay vì 20