from typing import List, Optional, Dict, Any
from .instruction import ISAInstruction


class ISAFunction:
    """Robot ISA function containing a sequence of instructions."""

    def __init__(
        self,
        name: str,
        entry_label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._name = name
        self._instructions: List[ISAInstruction] = []
        self._entry_label = entry_label or f"entry_{name}"
        self._metadata = metadata or {}
        self._labels: Dict[str, int] = {}  # label -> instruction index

    @property
    def name(self) -> str:
        return self._name

    @property
    def instructions(self) -> List[ISAInstruction]:
        return self._instructions

    @property
    def entry_label(self) -> str:
        return self._entry_label

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def size(self) -> int:
        return len(self._instructions)

    def add_instruction(self, instruction: ISAInstruction) -> None:
        self._instructions.append(instruction)

    def add_instructions(self, instructions: List[ISAInstruction]) -> None:
        self._instructions.extend(instructions)

    def add_label(self, label: str, index: int) -> None:
        self._labels[label] = index

    def get_label_index(self, label: str) -> Optional[int]:
        return self._labels.get(label)

    def has_label(self, label: str) -> bool:
        return label in self._labels

    def resolve_label(self, label: str, position: int) -> None:
        """Update label to point to current position (for forward references)."""
        self._labels[label] = position