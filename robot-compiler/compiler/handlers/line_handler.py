from ..generated.opcode import Opcode

class LineHandler:
    @staticmethod
    def line_intersection_stop(compiler, node):
        compiler.validate_argument_count(node, "line_intersection_stop", 2)
        speed = compiler.resolve_argument(node.args[0])
        type_ = compiler.resolve_argument(node.args[1])
        compiler.program.emit(Opcode.LineIntersectionStop.value, speed, type_, 0)