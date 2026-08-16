from ..generated.opcode import Opcode

class MotorHandler:
    @staticmethod
    def set_motor_straight_angle(compiler, node):
        compiler.validate_argument_count(node, "set_motor_straight_angle", 4)
        compiler.program.emit(Opcode.Nop.value, 0, 0, 0)

    @staticmethod
    def set_motor(compiler, node):
        compiler.validate_argument_count(node, "set_motor", 2)
        compiler.program.emit(Opcode.Nop.value, 0, 0, 0)

    @staticmethod
    def set_motor_servo(compiler, node):
        compiler.validate_argument_count(node, "set_motor_servo", 3)
        compiler.program.emit(Opcode.Nop.value, 0, 0, 0)