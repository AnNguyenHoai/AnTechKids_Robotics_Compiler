# runtime/context.py
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from .value import RuntimeValue
from .variable import VariableTable
from .stack import DataStack
from .frame import StackFrame

class ExecutionState(Enum):
    CREATED = "created"
    LOADED = "loaded"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"

@dataclass
class ExecutionContext:
    program_counter: int = 0
    call_stack: List[StackFrame] = field(default_factory=list)
    data_stack: DataStack = field(default_factory=DataStack)
    current_function_id: Optional[int] = None
    state: ExecutionState = ExecutionState.CREATED
    flags: int = 0
    registers: dict = field(default_factory=dict)
    global_vars: VariableTable = field(default_factory=VariableTable)
    local_vars: VariableTable = field(default_factory=VariableTable)

    def __post_init__(self):
        if self.call_stack is None:
            self.call_stack = []
        if self.registers is None:
            self.registers = {}
        if self.global_vars is None:
            self.global_vars = VariableTable()
        if self.local_vars is None:
            self.local_vars = VariableTable()

    def push_frame(self, frame: StackFrame):
        self.call_stack.append(frame)
        self.local_vars = frame.local_vars
        self.current_function_id = frame.function_id

    def pop_frame(self) -> StackFrame:
        if not self.call_stack:
            raise RuntimeError("No frame to pop")
        frame = self.call_stack.pop()
        if self.call_stack:
            self.local_vars = self.call_stack[-1].local_vars
            self.current_function_id = self.call_stack[-1].function_id
        else:
            self.local_vars = VariableTable()
            self.current_function_id = None
        return frame

    def top_frame(self) -> Optional[StackFrame]:
        return self.call_stack[-1] if self.call_stack else None