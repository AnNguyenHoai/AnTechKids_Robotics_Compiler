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

    def compile_ast(self, tree):
        self.program = Program()
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.temp_id = 0
        self.functions = {}
        self.loop_stack = []
        self.in_function = False
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

    # ----------------------------------------------------------
    # Expression compilation
    # ----------------------------------------------------------
    def compile_expression(self, expr):
        """Compile an expression and return variable index of result."""
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
        else:
            raise CompilerError(f"Unsupported expression type: {type(expr)}")

    def resolve_argument(self, arg):
        if isinstance(arg, ast.Name):
            return self.current_scope.resolve(arg.id)
        elif isinstance(arg, ast.Constant):
            index = self.allocate_temp()
            self.program.emit(Opcode.LoadConst.value, index, arg.value)
            return index
        elif isinstance(arg, (ast.BinOp, ast.UnaryOp)):
            return self.compile_expression(arg)
        else:
            raise CompilerError(f"Unsupported argument type: {type(arg)}")

    def validate_argument_count(self, node, function_name, expected):
        actual = len(node.args)
        if actual != expected:
            raise CompilerError(
                f"{function_name}() expects exactly {expected} argument(s)."
            )

    # ----------------------------------------------------------
    # AST Visitors
    # ----------------------------------------------------------
    # compiler/compiler.py - phần visit_Assign

    def visit_Assign(self, node):
        # Chỉ hỗ trợ gán cho một biến đơn
        if len(node.targets) != 1:
            raise CompilerError("Multiple assignment not supported.")
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise CompilerError("Only variable assignment supported.")
        name = target.id
        
        # Trường hợp 1: Gán hằng
        if isinstance(node.value, ast.Constant):
            value = node.value.value
            index = self.current_scope.allocate(name)
            self.program.emit(Opcode.LoadConst.value, index, value)
            return
        
        # Trường hợp 2: Gán biểu thức (BinOp hoặc UnaryOp)
        if isinstance(node.value, (ast.BinOp, ast.UnaryOp)):
            result = self.compile_expression(node.value)
            index = self.current_scope.allocate(name)
            self.program.emit(Opcode.Store.value, result, index, 0)
            return
        
        # Trường hợp 3: Gán biến (copy) - ví dụ: x = y
        if isinstance(node.value, ast.Name):
            src = self.current_scope.resolve(node.value.id)
            dest = self.current_scope.allocate(name)
            self.program.emit(Opcode.Store.value, src, dest, 0)
            return
        
        raise CompilerError(f"Only constant, expression, or variable assignment is supported. Got {type(node.value)}")

    def visit_FunctionDef(self, node):
        self.functions[node.name] = node
        return

    def visit_Expr(self, node):
        self.visit(node.value)

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise CompilerError(f"Unsupported function call: {ast.dump(node.func)}")
        func = node.func.id

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

    def visit_For(self, node):
        # Chỉ hỗ trợ for i in range(start, end, step) với step=1
        if not isinstance(node.iter, ast.Call):
            raise CompilerError("For loop only supports range()")
        if not isinstance(node.iter.func, ast.Name) or node.iter.func.id != 'range':
            raise CompilerError("For loop only supports range()")
        
        args = node.iter.args
        if len(args) == 1:
            start = 0
            end = self.compile_expression(args[0])
            step = 1
        elif len(args) == 2:
            start = self.compile_expression(args[0])
            end = self.compile_expression(args[1])
            step = 1
        elif len(args) == 3:
            start = self.compile_expression(args[0])
            end = self.compile_expression(args[1])
            step = self.compile_expression(args[2])
            # Đơn giản: chỉ hỗ trợ step=1
            if step != 1:
                raise CompilerError("Only step=1 is supported in for loop")
        else:
            raise CompilerError("range() requires 1-3 arguments")
        
        # Tên biến đếm
        target = node.target
        if not isinstance(target, ast.Name):
            raise CompilerError("For loop target must be a variable name")
        var_name = target.id
        var_index = self.current_scope.allocate(var_name)
        
        # Khởi tạo biến đếm = start
        self.program.emit(Opcode.LoadConst.value, var_index, start)
        
        # Labels
        begin_label = self.program.new_label()
        end_label = self.program.new_label()
        self.loop_stack.append({"begin": begin_label, "end": end_label})
        
        self.program.emit_label(begin_label)
        
        # So sánh: var_index < end
        temp = self.allocate_temp()
        self.program.emit(Opcode.CompareLT.value, var_index, end, temp)
        self.program.emit_jump_if_false(Opcode.JumpIfFalse.value, temp, end_label)
        
        # Thân vòng lặp
        for stmt in node.body:
            self.visit(stmt)
        
        # Tăng biến đếm lên 1
        temp2 = self.allocate_temp()
        self.program.emit(Opcode.LoadConst.value, temp2, 1)
        self.program.emit(Opcode.Add.value, var_index, temp2, temp)
        self.program.emit(Opcode.Store.value, temp, var_index, 0)
        
        self.program.emit_jump(Opcode.Jump.value, begin_label)
        
        self.loop_stack.pop()
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