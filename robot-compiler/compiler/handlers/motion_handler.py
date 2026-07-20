from ..generated.opcode import Opcode

class MotionHandler:
    @staticmethod
    def forward(compiler, node):
        index = compiler.resolve_argument(node.args[0])
        compiler.program.emit(Opcode.Forward.value, index)

    @staticmethod
    def backward(compiler, node):
        index = compiler.resolve_argument(node.args[0])
        compiler.program.emit(Opcode.Backward.value, index)

    @staticmethod
    def turn_left(compiler, node):
        index = compiler.resolve_argument(node.args[0])
        compiler.program.emit(Opcode.TurnLeft.value, index)

    @staticmethod
    def turn_right(compiler, node):
        index = compiler.resolve_argument(node.args[0])
        compiler.program.emit(Opcode.TurnRight.value, index)