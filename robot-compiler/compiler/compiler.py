import ast
from .handlers.compare_handler import CompareHandler
from .program import Program
from .scope import Scope
from .error import CompilerError
from .generated.function_registry import FUNCTION_REGISTRY
from .handlers.bool_handler import BoolHandler
from .generated.opcode import Opcode


class RobotCompiler(ast.NodeVisitor):

    def __init__(self):
        self.program = Program()
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.temp_id = 0
        self.functions = {}
        self.loop_stack = []
        self.in_function = False
        self._top_level_functions = {}

    def compile_ast(self, tree):
        self.program = Program()
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.temp_id = 0
        self.functions = {}
        self.loop_stack = []
        self.in_function = False
        self._top_level_functions = {}

        if not isinstance(tree, ast.Module):
            raise CompilerError("Compiler input must be a Python module.")

        # Pre-register all top-level function definitions before compiling
        # statements. This makes function calls independent of source order
        # while preserving the existing inline-function execution model.
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self._register_function_definition(node)
                self._top_level_functions[node.name] = node

        self.visit(tree)
        self.program.resolve_labels()
        return self.program

    def compile(self, filename):
        with open(filename, "r", encoding="utf8") as f:
            tree = ast.parse(f.read())
        return self.compile_ast(tree)

    def allocate_temp(self):
        name = f"__temp{self.temp_id}"
        self.temp_id += 1
        return self.current_scope.allocate(name)

    def allocate_result(self):
        return self.allocate_temp()

    def _get_semantic(self, func_name):
        """Get semantic classification for a function."""
        info = FUNCTION_REGISTRY.get(func_name)
        if info:
            return info.get("semantic", "Native")
        return "Native"

    # ----------------------------------------------------------
    # Expression compilation
    # ----------------------------------------------------------
    def compile_expression(self, expr):
        if isinstance(expr, ast.Constant):
            index = self.allocate_temp()
            self.program.emit(Opcode.LoadConst.value, index, expr.value)
            return index
        elif isinstance(expr, ast.Name):
            return self.current_scope.resolve(expr.id)
        elif isinstance(expr, ast.BinOp):
            left = self.compile_expression(expr.left)
            right = self.compile_expression(expr.right)
            result = self.allocate_temp()
            op_map = {
                ast.Add: Opcode.Add,
                ast.Sub: Opcode.Sub,
                ast.Mult: Opcode.Mul,
                ast.Div: Opcode.Div,
                ast.Mod: Opcode.Mod,
                ast.Pow: Opcode.Pow,
            }
            op = op_map.get(type(expr.op))
            if op is None:
                raise CompilerError(f"Unsupported binary operator: {type(expr.op).__name__}")
            self.program.emit(op.value, left, right, result)
            return result
        elif isinstance(expr, ast.UnaryOp):
            operand = self.compile_expression(expr.operand)
            result = self.allocate_temp()
            if isinstance(expr.op, ast.USub):
                self.program.emit(Opcode.Neg.value, operand, 0, result)
            else:
                raise CompilerError(f"Unsupported unary operator: {type(expr.op).__name__}")
            return result
        elif isinstance(expr, ast.Compare):
            return CompareHandler.compare(self, expr)
        elif isinstance(expr, ast.BoolOp):
            return BoolHandler.bool_op(self, expr)
        elif isinstance(expr, ast.Call):
            return self.compile_call_value(expr)
        else:
            raise CompilerError(f"Unsupported expression type: {type(expr).__name__}")

    def resolve_argument(self, arg):
        if isinstance(arg, ast.Name):
            return self.current_scope.resolve(arg.id)
        elif isinstance(arg, ast.Constant):
            index = self.allocate_temp()
            self.program.emit(Opcode.LoadConst.value, index, arg.value)
            return index
        elif isinstance(arg, (ast.BinOp, ast.UnaryOp, ast.Compare, ast.BoolOp, ast.Call)):
            return self.compile_expression(arg)
        else:
            raise CompilerError(f"Unsupported argument type: {type(arg).__name__}")

    def validate_argument_count(self, node, function_name, expected):
        actual = len(node.args)
        if actual != expected:
            raise CompilerError(
                f"{function_name}() expects exactly {expected} argument(s)."
            )

    def _validate_call(self, node, function_name):
        if node.keywords:
            raise CompilerError(
                f"{function_name}() does not support keyword arguments."
            )
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                raise CompilerError(
                    f"{function_name}() does not support starred arguments."
                )

    # ----------------------------------------------------------
    # AST Visitors
    # ----------------------------------------------------------

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def generic_visit(self, node):
        # Never silently ignore a Python construct that has no compiler
        # semantics. Operator/context nodes are normally consumed directly by
        # their parent compiler methods and are allowed here only for AST
        # traversal safety.
        if isinstance(node, (ast.operator, ast.unaryop, ast.boolop, ast.cmpop,
                             ast.expr_context)):
            return super().generic_visit(node)
        raise CompilerError(f"Unsupported syntax node: {type(node).__name__}")

    # ---------- Import ----------
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name not in ('rcu', '_thread'):
                raise CompilerError(f"Unsupported import: import {alias.name}")
            if alias.asname is not None:
                raise CompilerError(f"Import alias is not supported: import {alias.name} as {alias.asname}")
        return None

    def visit_ImportFrom(self, node):
        if node.module not in ('rcu', '_thread'):
            raise CompilerError(f"Unsupported import: from {node.module or ''} import ...")
        if node.level:
            raise CompilerError("Relative imports are not supported.")
        return None

    # ---------- _thread.start_new_thread ----------
    def visit_Expr(self, node):
        if (isinstance(node.value, ast.Call) and
            isinstance(node.value.func, ast.Attribute) and
            isinstance(node.value.func.value, ast.Name) and
            node.value.func.value.id == '_thread' and
            node.value.func.attr == 'start_new_thread'):
            if len(node.value.args) != 2:
                raise CompilerError("_thread.start_new_thread() expects a function and args tuple.")
            func = node.value.args[0]
            if not isinstance(func, ast.Name):
                raise CompilerError("_thread.start_new_thread() requires a function name.")
            if node.value.keywords:
                raise CompilerError("_thread.start_new_thread() does not support keyword arguments.")
            return self.visit(ast.Expr(ast.Call(func=func, args=[], keywords=[])))
        self.generic_visit(node)
        return node

    # ---------- Assign ----------
    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise CompilerError("Multiple assignment not supported.")
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise CompilerError("Only variable assignment supported.")
        name = target.id
        dest = self.current_scope.allocate(name)

        if isinstance(node.value, ast.Constant):
            self.program.emit(Opcode.LoadConst.value, dest, node.value.value)
            return

        if isinstance(node.value, ast.Name):
            src = self.current_scope.resolve(node.value.id)
            self.program.emit(Opcode.Store.value, src, dest, 0)
            return

        result = self.compile_expression(node.value)
        self.program.emit(Opcode.Store.value, result, dest, 0)

    # ---------- Function definition ----------
    def _register_function_definition(self, node):
        if node.name in self.functions:
            raise CompilerError(f"Duplicate function definition: '{node.name}()'.")
        if node.name in FUNCTION_REGISTRY:
            raise CompilerError(
                f"User-defined function '{node.name}()' conflicts with a built-in Robot API."
            )
        if node.args.args:
            raise CompilerError(
                f"User-defined function '{node.name}()' with parameters is not supported."
            )
        if node.args.vararg or node.args.kwarg or node.args.kwonlyargs:
            raise CompilerError(
                f"User-defined function '{node.name}()' with parameters is not supported."
            )
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return):
                raise CompilerError(
                    f"User-defined function '{node.name}()' cannot use return."
                )
        self.functions[node.name] = node

    def visit_FunctionDef(self, node):
        if self._top_level_functions.get(node.name) is not node:
            raise CompilerError("Nested function definitions are not supported.")
        return

    # ---------- Function call (statement level) ----------
    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise CompilerError(f"Unsupported function call: {ast.dump(node.func)}")
        func = node.func.id

        # User-defined function
        if func in self.functions:
            self._validate_call(node, func)
            function = self.functions[func]
            for stmt in function.body:
                self.visit(stmt)
            return

        # Built-in function - MUST exist in registry
        info = FUNCTION_REGISTRY.get(func)
        if info is None:
            raise CompilerError(f"Unknown function or Robot API: '{func}()'.")

        self._validate_call(node, func)
        expected = info.get("arguments", 0)
        actual = len(node.args)
        if actual != expected:
            raise CompilerError(f"{func}() expects exactly {expected} argument(s).")

        handler = info["handler"]
        handler(self, node)

    # ---------- Function call (expression level) ----------
    def compile_call_value(self, node):
        if not isinstance(node.func, ast.Name):
            raise CompilerError(f"Unsupported function call in expression: {ast.dump(node.func)}")
        func = node.func.id

        if func in self.functions:
            raise CompilerError(f"User-defined function '{func}()' cannot be used as a value")

        info = FUNCTION_REGISTRY.get(func)
        if info is None:
            raise CompilerError(f"Unknown function or Robot API: '{func}()'.")

        self._validate_call(node, func)
        expected = info.get("arguments", 0)
        actual = len(node.args)
        if actual != expected:
            raise CompilerError(f"{func}() expects exactly {expected} argument(s).")

        handler = info["handler"]
        result = handler(self, node)
        if result is None:
            raise CompilerError(f"Robot API '{func}()' does not return a value.")
        return result

    # ---------- Compare ----------
    def visit_Compare(self, node):
        return CompareHandler.compare(self, node)

    # ---------- BoolOp ----------
    def visit_BoolOp(self, node):
        return BoolHandler.bool_op(self, node)

    # ---------- Constant ----------
    def visit_Constant(self, node):
        return self.compile_expression(node)

    # ---------- Name ----------
    def visit_Name(self, node):
        return self.current_scope.resolve(node.id)

    # ---------- Return ----------
    def visit_Return(self, node):
        raise CompilerError("'return' is not supported by the RoboSim language.")

    # ---------- Pass ----------
    def visit_Pass(self, node):
        return

    # ---------- If ----------
    def visit_If(self, node):
        result = self.compile_expression(node.test)
        else_label = self.program.new_label()
        end_label = self.program.new_label()

        self.program.emit_jump_if_false(Opcode.JumpIfFalse.value, result, else_label)

        for stmt in node.body:
            self.visit(stmt)

        if len(node.orelse) > 0:
            self.program.emit_jump(Opcode.Jump.value, end_label)

        self.program.emit_label(else_label)

        for stmt in node.orelse:
            self.visit(stmt)

        self.program.emit_label(end_label)

    # ---------- For ----------
    def visit_For(self, node):
        if not isinstance(node.iter, ast.Call):
            raise CompilerError("For loop only supports range()")
        if not isinstance(node.iter.func, ast.Name) or node.iter.func.id != 'range':
            raise CompilerError("For loop only supports range()")

        args = node.iter.args
        if len(args) == 1:
            start = 0
            end = self.compile_expression(args[0])
        elif len(args) == 2:
            start = self.compile_expression(args[0])
            end = self.compile_expression(args[1])
        elif len(args) == 3:
            start = self.compile_expression(args[0])
            end = self.compile_expression(args[1])
            step_node = args[2]
            if not (
                isinstance(step_node, ast.Constant)
                and isinstance(step_node.value, (int, float))
                and not isinstance(step_node.value, bool)
                and step_node.value == 1
            ):
                raise CompilerError("Only range() step=1 is supported in for loop")
        else:
            raise CompilerError("range() requires 1-3 arguments")

        target = node.target
        if not isinstance(target, ast.Name):
            raise CompilerError("For loop target must be a variable name")
        var_name = target.id
        var_index = self.current_scope.allocate(var_name)

        self.program.emit(Opcode.LoadConst.value, var_index, start)

        begin_label = self.program.new_label()
        end_label = self.program.new_label()
        self.loop_stack.append({"begin": begin_label, "end": end_label})

        self.program.emit_label(begin_label)

        temp = self.allocate_temp()
        self.program.emit(Opcode.CompareLT.value, var_index, end, temp)
        self.program.emit_jump_if_false(Opcode.JumpIfFalse.value, temp, end_label)

        for stmt in node.body:
            self.visit(stmt)

        temp2 = self.allocate_temp()
        self.program.emit(Opcode.LoadConst.value, temp2, 1)
        self.program.emit(Opcode.Add.value, var_index, temp2, temp)
        self.program.emit(Opcode.Store.value, temp, var_index, 0)

        self.program.emit_jump(Opcode.Jump.value, begin_label)

        self.loop_stack.pop()
        self.program.emit_label(end_label)

    # ---------- While ----------
    def visit_While(self, node):
        if (isinstance(node.test, ast.Constant) and node.test.value in (True, 1) and
            len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
            return

        begin_label = self.program.new_label()
        end_label = self.program.new_label()
        self.loop_stack.append({"begin": begin_label, "end": end_label})
        self.program.emit_label(begin_label)

        if not (isinstance(node.test, ast.Constant) and node.test.value in (True, 1)):
            result = self.compile_expression(node.test)
            self.program.emit_jump_if_false(Opcode.JumpIfFalse.value, result, end_label)

        for stmt in node.body:
            self.visit(stmt)

        self.program.emit_jump(Opcode.Jump.value, begin_label)

        self.loop_stack.pop()
        self.program.emit_label(end_label)

    # ---------- Break ----------
    def visit_Break(self, node):
        if len(self.loop_stack) == 0:
            raise CompilerError("'break' outside loop.")
        context = self.loop_stack[-1]
        self.program.emit_jump(Opcode.Jump.value, context["end"])

    # ---------- Continue ----------
    def visit_Continue(self, node):
        if len(self.loop_stack) == 0:
            raise CompilerError("'continue' outside loop.")
        context = self.loop_stack[-1]
        self.program.emit_jump(Opcode.Jump.value, context["begin"])
