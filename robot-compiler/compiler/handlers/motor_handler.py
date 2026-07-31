from ..generated.opcode import Opcode

class MotorHandler:
    @staticmethod
    def set_motor_straight_angle(compiler, node):
        compiler.validate_argument_count(node, "set_motor_straight_angle", 4)
        left_port = compiler.resolve_argument(node.args[0])
        right_port = compiler.resolve_argument(node.args[1])
        speed = compiler.resolve_argument(node.args[2])
        angle = compiler.resolve_argument(node.args[3])
        # Emit với 4 tham số: p1=left_port, p2=right_port, p3=speed, p4=angle
        compiler.program.emit(Opcode.SetMotorStraightAngle.value, left_port, right_port, speed, angle)