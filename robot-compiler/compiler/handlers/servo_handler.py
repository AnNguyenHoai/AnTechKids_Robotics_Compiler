from ..generated.opcode import Opcode

class ServoHandler:
    @staticmethod
    def set_servo(compiler, node):
        compiler.validate_argument_count(node, "set_servo", 2)
        port = compiler.resolve_argument(node.args[0])
        angle = compiler.resolve_argument(node.args[1])
        compiler.program.emit(Opcode.SetServo.value, port, angle, 0)