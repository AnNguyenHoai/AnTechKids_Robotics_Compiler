from __future__ import annotations
from typing import List, Optional, Dict, Any
from .value import IRValue
from .basic_block import IRBasicBlock


class IRFunction:
    def __init__(self, name: str,
                 arguments: Optional[List[IRValue]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.arguments = arguments if arguments is not None else []
        self.blocks: List[IRBasicBlock] = []
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"IRFunction(name='{self.name}', blocks={len(self.blocks)})"

    def add_block(self, block: IRBasicBlock) -> None:
        self.blocks.append(block)

    def entry_block(self) -> Optional[IRBasicBlock]:
        return self.blocks[0] if self.blocks else None

    def size(self) -> int:
        return sum(b.size() for b in self.blocks)