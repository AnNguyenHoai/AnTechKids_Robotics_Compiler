
from dataclasses import dataclass

@dataclass
class Instruction:
    opcode: int
    p1: int = 0
    p2: int = 0
    p3: int = 0