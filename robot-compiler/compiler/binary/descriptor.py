# compiler/binary/descriptor.py
from typing import List, Optional

class OpcodeDescriptor:
    def __init__(
        self,
        number: int,
        mnemonic: str,
        operand_count: int,
        operand_types: List[str],
        encoding_size: int,
        description: str = ""
    ):
        self.number = number
        self.mnemonic = mnemonic
        self.operand_count = operand_count
        self.operand_types = operand_types
        self.encoding_size = encoding_size
        self.description = description

    def __repr__(self):
        return f"OpcodeDescriptor({self.mnemonic}, #{self.number})"