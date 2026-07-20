from ..generated.opcode import Opcode

class SystemHandler:
    @staticmethod
    def wait(compiler, node):
        compiler.validate_argument_count(node, "wait", 1)
        index = compiler.resolve_argument(node.args[0])
        compiler.program.emit(Opcode.Wait.value, index)

    @staticmethod
    def stop(compiler, node):
        compiler.validate_argument_count(node, "stop", 0)
        compiler.program.emit(Opcode.Stop.value)