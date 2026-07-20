import ast

from .handlers.compare_handler import CompareHandler
from .program import Program
from .symbol_table import SymbolTable
from .opcode import OpcodeTable
from .error import CompilerError
from .generated.function_registry import FUNCTION_REGISTRY
from .handlers.bool_handler import BoolHandler



class RobotCompiler(ast.NodeVisitor):

    def __init__(self):

        self.program = Program()

        self.symbols = SymbolTable()

        self.opcodes = OpcodeTable()

        self.temp_id = 0
        self.functions = {}
        #
        # Compiler Context
        #
        self.loop_stack = []


    def compile_ast(self, tree):

        self.program = Program()
        self.symbols = SymbolTable()
        self.temp_id = 0
        self.functions = {}
        #
        # Reset compiler context
        #
        self.loop_stack = []

        self.visit(tree)

        self.program.resolve_labels()

        return self.program

    def compile(self, filename):

        with open(filename, "r", encoding="utf8") as f:
            tree = ast.parse(f.read())

        return self.compile_ast(tree)
    ##########################################################
    # Temporary Variable
    ##########################################################

    def allocate_temp(self):

        name = f"__temp{self.temp_id}"

        self.temp_id += 1

        return self.symbols.allocate(name)


    ##########################################################
    # Resolve Function Argument
    ##########################################################

    def resolve_argument(self, arg):

        #
        # Variable
        #
        if isinstance(arg, ast.Name):

            return self.symbols.resolve(arg.id)

        #
        # Constant
        #
        elif isinstance(arg, ast.Constant):

            index = self.allocate_temp()

            self.program.emit(

                self.opcodes.get("LoadConst"),

                index,

                arg.value

            )

            return index

        #
        # Unsupported
        #
        else:

            raise Exception(
                f"Unsupported argument : {type(arg)}"
            )   

    ##########################################################
    # Validate
    ##########################################################

    def validate_argument_count(
        self,
        node,
        function_name,
        expected
    ):

        actual = len(node.args)

        if actual != expected:

            raise CompilerError(

                f"{function_name}() expects exactly {expected} argument(s)."

            )         
    ##########################################################
    # Variable
    ##########################################################

    def visit_Assign(self, node):

        name = node.targets[0].id

        value = node.value.value

        index = self.symbols.allocate(name)

        self.program.emit(

            self.opcodes.get("LoadConst"),

            index,

            value

        )
    ##########################################################
    # Function Definition
    ##########################################################

    def visit_FunctionDef(self, node):

        #
        # Chỉ lưu AST
        #
        self.functions[node.name] = node

        #
        # Không compile ngay
        #
        return
    ##########################################################
    # Function
    ##########################################################

    def visit_Expr(self, node):

        self.visit(node.value)

    def visit_Call(self, node):

        if not isinstance(node.func, ast.Name):

            raise CompilerError(

                f"Unsupported function call: {ast.dump(node.func)}"

            )
        func = node.func.id
        #
        # User function
        #
        if func in self.functions:

            function = self.functions[func]

            for stmt in function.body:

                self.visit(stmt)

            return        
        info = FUNCTION_REGISTRY.get(func)

        if info is None:
            raise CompilerError(
                f"Unknown function '{func}()'"
            )

        #
        # Validate argument count
        #
        expected = info["arguments"]

        actual = len(node.args)

        if actual != expected:
            raise CompilerError(
                f"{func}() expects exactly {expected} argument(s)."
            )

        #
        # Dispatch handler
        #
        handler = info["handler"]

        handler(
            self,
            node
        )
    ##########################################################

    ##########################################################
    # Expression
    ##########################################################
    def allocate_result(self):
        return self.allocate_temp()  
    
    def visit_Compare(self, node):

        return CompareHandler.compare(
            self,
            node
        )
    def visit_BoolOp(self, node):

        return BoolHandler.bool_op(
            self,
            node
        )    
    ##########################################################
    # If
    ##########################################################

    def visit_If(self, node):

        #
        # Compile condition
        #
        result = self.visit(node.test)

        #
        # Create labels
        #
        else_label = self.program.new_label()

        end_label = self.program.new_label()

        #
        # Jump to else if condition == false
        #
        self.program.emit_jump_if_false(

            self.opcodes.get("JumpIfFalse"),

            result,

            else_label

        )

        #
        # True branch
        #
        for stmt in node.body:

            self.visit(stmt)

        #
        # Skip else branch
        #
        if len(node.orelse) > 0:

            self.program.emit_jump(

                self.opcodes.get("Jump"),

                end_label

            )

        #
        # Else label
        #
        self.program.emit_label(
            else_label
        )

        #
        # False branch
        #
        for stmt in node.orelse:

            self.visit(stmt)

        #
        # End label
        #
        self.program.emit_label(
            end_label
        )

    ##########################################################
    # While
    ##########################################################

    def visit_While(self, node):

        #
        # Begin label
        #
        begin_label = self.program.new_label()

        #
        # End label
        #
        end_label = self.program.new_label()
        #
        # Enter loop context
        #
        self.loop_stack.append({

            "begin": begin_label,

            "end": end_label

        })
        #
        # Mark begin
        #
        self.program.emit_label(
            begin_label
        )

        #
        # Compile condition
        #
        result = self.visit(
            node.test
        )

        #
        # Exit if false
        #
        self.program.emit_jump_if_false(

            self.opcodes.get("JumpIfFalse"),

            result,

            end_label

        )

        #
        # Compile body
        #
        for stmt in node.body:

            self.visit(stmt)

        #
        # Jump back
        #
        self.program.emit_jump(

            self.opcodes.get("Jump"),

            begin_label

        )
        #
        # Leave loop context
        #
        self.loop_stack.pop()

        #
        # End label
        #
        self.program.emit_label(
            end_label
        )

    ##########################################################
    # Break
    ##########################################################

    def visit_Break(self, node):

        #
        # Must be inside a loop
        #
        if len(self.loop_stack) == 0:

            raise CompilerError(
                "'break' outside loop."
            )

        context = self.loop_stack[-1]

        self.program.emit_jump(

            self.opcodes.get("Jump"),

            context["end"]

        )

    ##########################################################
    # Continue
    ##########################################################

    def visit_Continue(self, node):

        #
        # Must be inside a loop
        #
        if len(self.loop_stack) == 0:

            raise CompilerError(
                "'continue' outside loop."
            )

        context = self.loop_stack[-1]

        self.program.emit_jump(

            self.opcodes.get("Jump"),

            context["begin"]

        )











