# runtime/engine.py
from typing import Optional
from .context import ExecutionContext, ExecutionState
from .value import RuntimeValue, IntegerValue, FloatValue, BooleanValue, StringValue, ReferenceValue
from .variable import VariableTable
from .stack import DataStack
from .frame import StackFrame
from .program import RuntimeProgram
from .iterator import InstructionIterator
from .exceptions import InvalidInstructionException

class ExecutionEngine:
    def __init__(self):
        self.context = ExecutionContext()
        self.program: Optional[RuntimeProgram] = None
        self.iterator: Optional[InstructionIterator] = None

    def load(self, program: RuntimeProgram):
        self.program = program
        self.context = ExecutionContext()
        self.iterator = InstructionIterator(program, function_id=0)
        self.context.program_counter = 0
        self.context.state = ExecutionState.LOADED
        # Khởi tạo global vars
        self.context.global_vars = VariableTable()

    # --- Stack operations ---
    def push(self, value: RuntimeValue):
        self.context.data_stack.push(value)

    def pop(self) -> RuntimeValue:
        return self.context.data_stack.pop()

    def peek(self) -> Optional[RuntimeValue]:
        return self.context.data_stack.peek()

    # --- Variable operations ---
    def get_variable(self, name: str) -> Optional[RuntimeValue]:
        if self.context.local_vars and self.context.local_vars.has(name):
            return self.context.local_vars.get(name)
        return self.context.global_vars.get(name)

    def get_variable_by_index(self, index: int) -> RuntimeValue:
        name = f"v{index}"
        val = self.get_variable(name)
        if val is None:
            raise KeyError(f"Variable '{name}' not found")
        return val

    def set_variable(self, name: str, value: RuntimeValue):
        if self.context.local_vars and self.context.local_vars.has(name):
            self.context.local_vars.set(name, value)
        elif self.context.global_vars.has(name):
            self.context.global_vars.set(name, value)
        else:
            # Tự động tạo global nếu chưa có
            self.context.global_vars.define(name, value)

    def set_variable_by_index(self, index: int, value: RuntimeValue):
        name = f"v{index}"
        self.set_variable(name, value)

    def define_global(self, name: str, value: RuntimeValue = None):
        self.context.global_vars.define(name, value)

    def define_local(self, name: str, value: RuntimeValue = None):
        if self.context.local_vars:
            self.context.local_vars.define(name, value)
        else:
            raise RuntimeError("No local scope")

    # --- Control flow ---
    def jump(self, target: int):
        if target < 0 or target > self.iterator.size:
            raise ValueError(f"Invalid jump target: {target}")
        self.context.program_counter = target
        self.iterator.seek(target)

    def call(self, function_id: int):
        func = self.program.get_function(function_id)
        if func is None:
            raise ValueError(f"Function {function_id} not found")
        # Tạo frame mới với local vars
        frame = StackFrame(
            function_id=function_id,
            return_address=self.context.program_counter + 1,
            local_vars=VariableTable()
        )
        self.context.push_frame(frame)
        self.context.program_counter = func.entry_index
        self.iterator.seek(func.entry_index)

    def return_(self):
        if not self.context.call_stack:
            raise RuntimeError("Return without call")
        frame = self.context.pop_frame()
        self.context.program_counter = frame.return_address
        self.iterator.seek(frame.return_address)

    # --- Comparison ---
    def compare(self, left: RuntimeValue, right: RuntimeValue, op: str) -> BooleanValue:
        if isinstance(left, (IntegerValue, FloatValue)) and isinstance(right, (IntegerValue, FloatValue)):
            l = left.as_float()
            r = right.as_float()
        elif isinstance(left, BooleanValue) and isinstance(right, BooleanValue):
            l = left.as_bool()
            r = right.as_bool()
        elif isinstance(left, StringValue) and isinstance(right, StringValue):
            l = left.as_string()
            r = right.as_string()
        else:
            raise TypeError(f"Cannot compare {type(left)} and {type(right)}")
        
        if op == "==":
            return BooleanValue(l == r)
        elif op == "!=":
            return BooleanValue(l != r)
        elif op == ">":
            return BooleanValue(l > r)
        elif op == ">=":
            return BooleanValue(l >= r)
        elif op == "<":
            return BooleanValue(l < r)
        elif op == "<=":
            return BooleanValue(l <= r)
        else:
            raise ValueError(f"Unknown comparison operator: {op}")

    # --- Arithmetic ---
    def add(self, left: RuntimeValue, right: RuntimeValue) -> RuntimeValue:
        if isinstance(left, IntegerValue) and isinstance(right, IntegerValue):
            return IntegerValue(left.as_int() + right.as_int())
        elif isinstance(left, (IntegerValue, FloatValue)) and isinstance(right, (IntegerValue, FloatValue)):
            return FloatValue(left.as_float() + right.as_float())
        elif isinstance(left, StringValue) and isinstance(right, StringValue):
            return StringValue(left.as_string() + right.as_string())
        else:
            raise TypeError("Unsupported addition")

    def sub(self, left: RuntimeValue, right: RuntimeValue) -> RuntimeValue:
        if isinstance(left, IntegerValue) and isinstance(right, IntegerValue):
            return IntegerValue(left.as_int() - right.as_int())
        elif isinstance(left, (IntegerValue, FloatValue)) and isinstance(right, (IntegerValue, FloatValue)):
            return FloatValue(left.as_float() - right.as_float())
        else:
            raise TypeError("Unsupported subtraction")

    def mul(self, left: RuntimeValue, right: RuntimeValue) -> RuntimeValue:
        if isinstance(left, IntegerValue) and isinstance(right, IntegerValue):
            return IntegerValue(left.as_int() * right.as_int())
        elif isinstance(left, (IntegerValue, FloatValue)) and isinstance(right, (IntegerValue, FloatValue)):
            return FloatValue(left.as_float() * right.as_float())
        else:
            raise TypeError("Unsupported multiplication")

    def div(self, left: RuntimeValue, right: RuntimeValue) -> RuntimeValue:
        if isinstance(left, IntegerValue) and isinstance(right, IntegerValue):
            if right.as_int() == 0:
                raise ZeroDivisionError("Division by zero")
            return IntegerValue(left.as_int() // right.as_int())
        elif isinstance(left, (IntegerValue, FloatValue)) and isinstance(right, (IntegerValue, FloatValue)):
            if right.as_float() == 0.0:
                raise ZeroDivisionError("Division by zero")
            return FloatValue(left.as_float() / right.as_float())
        else:
            raise TypeError("Unsupported division")

    def mod(self, left: RuntimeValue, right: RuntimeValue) -> RuntimeValue:
        if isinstance(left, IntegerValue) and isinstance(right, IntegerValue):
            if right.as_int() == 0:
                raise ZeroDivisionError("Modulo by zero")
            return IntegerValue(left.as_int() % right.as_int())
        else:
            raise TypeError("Modulo only supported for integers")

    def pow(self, left: RuntimeValue, right: RuntimeValue) -> RuntimeValue:
        if isinstance(left, IntegerValue) and isinstance(right, IntegerValue):
            return IntegerValue(left.as_int() ** right.as_int())
        else:
            raise TypeError("Power only supported for integers")

    def neg(self, value: RuntimeValue) -> RuntimeValue:
        if isinstance(value, IntegerValue):
            return IntegerValue(-value.as_int())
        elif isinstance(value, FloatValue):
            return FloatValue(-value.as_float())
        else:
            raise TypeError("Negation only supported for numbers")