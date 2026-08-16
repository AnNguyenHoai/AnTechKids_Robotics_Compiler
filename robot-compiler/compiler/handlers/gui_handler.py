from ..generated.opcode import Opcode

class GuiHandler:
    @staticmethod
    def update_var(compiler, node):
        # NOP: GUI-only API, no runtime code
        compiler.validate_argument_count(node, "update_var", 2)
        # No bytecode emitted - NOP at runtime

    @staticmethod
    def display_variable(compiler, node):
        # NOP: GUI-only API, no runtime code
        compiler.validate_argument_count(node, "display_variable", 1)
        # No bytecode emitted - NOP at runtime