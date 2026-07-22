from dataclasses import dataclass

@dataclass
class ExpectedInstruction:

    opcode: str

    p1: int

    p2: int

    p3: int