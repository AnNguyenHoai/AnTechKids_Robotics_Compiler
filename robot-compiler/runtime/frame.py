# runtime/frame.py
from typing import Optional
from .variable import VariableTable

class StackFrame:
    def __init__(self, function_id: int, return_address: int, local_vars: VariableTable):
        self.function_id = function_id
        self.return_address = return_address
        self.local_vars = local_vars
        self.previous_frame: Optional['StackFrame'] = None