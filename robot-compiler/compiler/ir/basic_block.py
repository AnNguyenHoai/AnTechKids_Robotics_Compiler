from __future__ import annotations
from typing import List, Optional, Set
from .instruction import IRInstruction


class IRBasicBlock:
    def __init__(self, label: Optional[str] = None):
        self.label = label
        self.instructions: List[IRInstruction] = []
        self.predecessors: Set[IRBasicBlock] = set()
        self.successors: Set[IRBasicBlock] = set()

    def __repr__(self) -> str:
        return f"IRBasicBlock(label='{self.label}', instructions={len(self.instructions)})"

    def append(self, instruction: IRInstruction) -> None:
        self.instructions.append(instruction)

    def extend(self, instructions: List[IRInstruction]) -> None:
        self.instructions.extend(instructions)

    def size(self) -> int:
        return len(self.instructions)

    def is_empty(self) -> bool:
        return len(self.instructions) == 0

    def add_successor(self, block: IRBasicBlock) -> None:
        self.successors.add(block)
        block.predecessors.add(self)