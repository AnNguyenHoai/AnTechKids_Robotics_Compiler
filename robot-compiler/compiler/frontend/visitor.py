import ast
from pathlib import Path
from typing import Optional
from ..ir import IRBuilder, IRValue, IRProgram, IRFunction, IRBasicBlock, IROpcode, SourceLocation, ValueKind
from .errors import CompilerError


class ASTVisitor(ast.NodeVisitor):
    def __init__(self, source_path: Path):
        self.source_path = source_path
        self.builder = IRBuilder()
        self._function_stack: list[str] = []
        self._current_func_name: Optional[str] = None

    def compile(self) -> IRProgram:
        return self.builder.get_program()

    def _loc(self, node: ast.AST) -> SourceLocation:
        return SourceLocation(str(self.source_path), node.lineno, node.col_offset)

    # ----- Ignore imports -----
    def visit_Import(self, node: ast.Import):
        pass

    def visit_ImportFrom(self, node: ast.ImportFrom):
        pass

    # ----- Module -----
    def visit_Module(self, node: ast.Module):
        self.builder.create_function("main")
        self.builder.create_block("entry")
        self._current_func_name = "main"

        for stmt in node.body:
            self.visit(stmt)

    # ----- Function Definitions -----
    def visit_FunctionDef(self, node: ast.FunctionDef):
        func_name = node.name
        self._function_stack.append(func_name)
        func = self.builder.create_function(func_name)
        entry = self.builder.create_block("entry")
        self._current_func_name = func_name
        for stmt in node.body:
            self.visit(stmt)
        self._function_stack.pop()
        if len(self._function_stack) > 0:
            self._current_func_name = self._function_stack[-1]
        else:
            self._current_func_name = "main"

    # ----- Expression Statements (calls) -----
    def visit_Expr(self, node: ast.Expr):
        self.visit(node.value)

    # ----- Function Calls -----
    def visit_Call(self, node: ast.Call):
        # Check if it's a RoboSim API call (rcu.xxx)
        if isinstance(node.func, ast.Attribute):
            receiver = node.func.value
            method = node.func.attr
            if isinstance(receiver, ast.Name) and receiver.id == "rcu":
                self._handle_rcu_call(method, node)
                return

        # Check if it's a built-in API (forward, stop, etc.)
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ("forward", "backward", "turn_left", "turn_right", "wait", "stop"):
                self._handle_builtin_call(func_name, node)
                return
            # Otherwise, it's a user-defined function call
            self._handle_user_call(func_name, node)
            return

        # Unsupported call
        raise CompilerError(f"Unsupported function call: {ast.dump(node.func)}", self._loc(node))

    def _handle_rcu_call(self, method: str, node: ast.Call):
        loc = self._loc(node)
        if method == "SetMoveRun":
            if len(node.args) != 2:
                raise CompilerError("SetMoveRun expects exactly 2 arguments", loc)
            direction = self._eval_arg(node.args[0])
            speed = self._eval_arg(node.args[1])
            self.builder.move_run(direction, speed, loc)

        elif method == "SetMoveRunSecond":
            if len(node.args) != 3:
                raise CompilerError("SetMoveRunSecond expects exactly 3 arguments", loc)
            direction = self._eval_arg(node.args[0])
            speed = self._eval_arg(node.args[1])
            seconds = self._eval_arg(node.args[2])
            if seconds.kind == ValueKind.INTEGER:
                ms = seconds.value * 1000
            elif seconds.kind == ValueKind.FLOAT:
                ms = int(seconds.value * 1000)
            else:
                raise CompilerError("SetMoveRunSecond expects numeric duration", loc)
            duration = self.builder.const_int(ms)
            self.builder.move_run_time(direction, speed, duration, loc)

        elif method == "SetMoveStop":
            if len(node.args) != 0:
                raise CompilerError("SetMoveStop expects 0 arguments", loc)
            self.builder.move_stop(loc)

        elif method == "SetWaitForTime":
            if len(node.args) != 1:
                raise CompilerError("SetWaitForTime expects exactly 1 argument", loc)
            seconds = self._eval_arg(node.args[0])
            if seconds.kind == ValueKind.INTEGER:
                ms = seconds.value * 1000
            elif seconds.kind == ValueKind.FLOAT:
                ms = int(seconds.value * 1000)
            else:
                raise CompilerError("SetWaitForTime expects numeric duration", loc)
            duration = self.builder.const_int(ms)
            self.builder.wait(duration, loc)

        else:
            raise CompilerError(f"Unknown RoboSim API: rcu.{method}()", loc)

    def _handle_builtin_call(self, func_name: str, node: ast.Call):
        loc = self._loc(node)
        if func_name == "forward":
            if len(node.args) != 1:
                raise CompilerError("forward expects exactly 1 argument (speed)", loc)
            speed = self._eval_arg(node.args[0])
            direction = self.builder.const_string("forward")
            self.builder.move_run(direction, speed, loc)
        elif func_name == "backward":
            if len(node.args) != 1:
                raise CompilerError("backward expects exactly 1 argument (speed)", loc)
            speed = self._eval_arg(node.args[0])
            direction = self.builder.const_string("backward")
            self.builder.move_run(direction, speed, loc)
        elif func_name == "turn_left":
            if len(node.args) != 1:
                raise CompilerError("turn_left expects exactly 1 argument (speed)", loc)
            speed = self._eval_arg(node.args[0])
            direction = self.builder.const_string("left")
            self.builder.move_run(direction, speed, loc)
        elif func_name == "turn_right":
            if len(node.args) != 1:
                raise CompilerError("turn_right expects exactly 1 argument (speed)", loc)
            speed = self._eval_arg(node.args[0])
            direction = self.builder.const_string("right")
            self.builder.move_run(direction, speed, loc)
        elif func_name == "wait":
            if len(node.args) != 1:
                raise CompilerError("wait expects exactly 1 argument (milliseconds)", loc)
            duration = self._eval_arg(node.args[0])
            self.builder.wait(duration, loc)
        elif func_name == "stop":
            if len(node.args) != 0:
                raise CompilerError("stop expects 0 arguments", loc)
            self.builder.move_stop(loc)
        else:
            raise CompilerError(f"Unknown built-in API: {func_name}()", loc)

    def _handle_user_call(self, func_name: str, node: ast.Call):
        loc = self._loc(node)
        func_val = self.builder.const_string(func_name)
        self.builder.call(func_val, loc)

    def _eval_arg(self, arg: ast.AST) -> IRValue:
        if isinstance(arg, ast.Constant):
            val = arg.value
            if isinstance(val, int):
                return self.builder.const_int(val)
            elif isinstance(val, float):
                return self.builder.const_float(val)
            elif isinstance(val, str):
                return self.builder.const_string(val)
            elif isinstance(val, bool):
                return self.builder.const_bool(val)
        elif isinstance(arg, ast.Name):
            return self.builder.var(arg.id)
        else:
            raise CompilerError(f"Unsupported argument type: {type(arg)}", self._loc(arg))
        raise CompilerError(f"Unsupported argument: {ast.dump(arg)}", self._loc(arg))

    # ----- Assign -----
    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) != 1:
            raise CompilerError("Multiple assignment not supported", self._loc(node))
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise CompilerError("Only simple variable assignment supported", self._loc(node))
        # For now, ignore assignment
        pass

    # ----- Pass statement -----
    def visit_Pass(self, node: ast.Pass):
        pass

    # ----- Unsupported nodes -----
    def generic_visit(self, node: ast.AST):
        raise CompilerError(f"Unsupported AST node: {type(node).__name__}", self._loc(node))