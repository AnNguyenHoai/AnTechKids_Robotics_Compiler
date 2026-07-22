# compiler/binary/header.py
import struct
from dataclasses import dataclass
from enum import IntEnum

class Magic(IntEnum):
    ROBOT_BINARY = 0x4E494252

class Endianness(IntEnum):
    LITTLE = 0
    BIG = 1

HEADER_FORMAT = "<IBBIBII"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

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
            HEADER_FORMAT,
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
        # data phải có ít nhất HEADER_SIZE bytes
        values = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
        return cls(*values)

    def size(self) -> int:
        return HEADER_SIZE