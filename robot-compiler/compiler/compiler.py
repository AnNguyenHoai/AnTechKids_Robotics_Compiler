import ast
from .handlers.compare_handler import CompareHandler
from .program import Program
from .symbol_table import SymbolTable
from .error import CompilerError
from .generated.function_registry import FUNCTION_REGISTRY
from .handlers.bool_handler import BoolHandler
from .generated.opcode import Opcode


class RobotCompiler(ast.NodeVisitor):
    def __init__(self):
        self.program = Program()
        self.symbols = SymbolTable()
        self.temp_id = 0
        self.functions = {}
        self.loop_stack = []

    def compile_ast(self, tree):
        self.program = Program()
        self.symbols = SymbolTable()
        self.temp_id = 0
        self.functions = {}
        self.loop_stack = []
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
        return self.symbols.allocate(name)

    def resolve_argument(self, arg):
        if isinstance(arg, ast.Name):
            return self.symbols.resolve(arg.id)
        elif isinstance(arg, ast.Constant):
            index = self.allocate_temp()
            self.program.emit(Opcode.LoadConst.value, index, arg.value)
            return index
        else:
            raise CompilerError(f"Unsupported argument type: {type(arg)}")

    def validate_argument_count(self, node, function_name, expected):
        actual = len(node.args)
        if actual != expected:
            raise CompilerError(
                f"{function_name}() expects exactly {expected} argument(s)."
            )

    def visit_Assign(self, node):
        name = node.targets[0].id
        value = node.value.value
        index = self.symbols.allocate(name)
        self.program.emit(Opcode.LoadConst.value, index, value)

    def visit_FunctionDef(self, node):
        self.functions[node.name] = node
        return

    def visit_Expr(self, node):
        self.visit(node.value)

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise CompilerError(f"Unsupported function call: {ast.dump(node.func)}")
        func = node.func.id

        # User function
        if func in self.functions:
            function = self.functions[func]
            for stmt in function.body:
                self.visit(stmt)
            return

        info = FUNCTION_REGISTRY.get(func)
        if info is None:
            raise CompilerError(f"Unknown function '{func}()'")

        expected = info["arguments"]
        actual = len(node.args)
        if actual != expected:
            raise CompilerError(f"{func}() expects exactly {expected} argument(s).")

        handler = info["handler"]
        handler(self, node)

    def allocate_result(self):
        return self.allocate_temp()

    def visit_Compare(self, node):
        return CompareHandler.compare(self, node)

    def visit_BoolOp(self, node):
        return BoolHandler.bool_op(self, node)

    def visit_If(self, node):
        result = self.visit(node.test)
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

    def visit_While(self, node):
        begin_label = self.program.new_label()
        end_label = self.program.new_label()
        self.loop_stack.append({"begin": begin_label, "end": end_label})
        self.program.emit_label(begin_label)
        result = self.visit(node.test)
        self.program.emit_jump_if_false(Opcode.JumpIfFalse.value, result, end_label)
        for stmt in node.body:
            self.visit(stmt)
        self.program.emit_jump(Opcode.Jump.value, begin_label)
        self.loop_stack.pop()
        self.program.emit_label(end_label)

    def visit_Break(self, node):
        if len(self.loop_stack) == 0:
            raise CompilerError("'break' outside loop.")
        context = self.loop_stack[-1]
        self.program.emit_jump(Opcode.Jump.value, context["end"])

    def visit_Continue(self, node):
        if len(self.loop_stack) == 0:
            raise CompilerError("'continue' outside loop.")
        context = self.loop_stack[-1]
        self.program.emit_jump(Opcode.Jump.value, context["begin"])