from ..generated.opcode import Opcode

class LineHandler:
    @staticmethod
    def line_intersection_stop(compiler, node):
        compiler.validate_argument_count(node, "line_intersection_stop", 2)
        speed = compiler.resolve_argument(node.args[0])
        type_ = compiler.resolve_argument(node.args[1])
        compiler.program.emit(Opcode.LineIntersectionStop.value, speed, type_, 0)
    @staticmethod
    def line_basis(compiler, node):
        compiler.validate_argument_count(node, "line_basis", 1)
        speed = compiler.resolve_argument(node.args[0])
        compiler.program.emit(Opcode.LineBasis.value, speed, 0, 0)

    @staticmethod
    def line_follow(compiler, node):
        compiler.validate_argument_count(node, "line_follow", 1)
        speed = compiler.resolve_argument(node.args[0])
        compiler.program.emit(Opcode.LineFollow.value, speed, 0, 0)

    @staticmethod
    def line_stop(compiler, node):
        compiler.validate_argument_count(node, "line_stop", 0)
        compiler.program.emit(Opcode.LineStop.value, 0, 0, 0)