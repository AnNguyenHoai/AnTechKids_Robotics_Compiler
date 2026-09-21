from ..generated.opcode import Opcode

class MotorHandler:
    @staticmethod
    def set_motor_straight_angle(compiler, node):
        # Stub: accepted by the language, intentionally emits no runtime bytecode.
        compiler.validate_argument_count(node, "set_motor_straight_angle", 4)

    @staticmethod
    def set_motor(compiler, node):
        # Stub: accepted by the language, intentionally emits no runtime bytecode.
        compiler.validate_argument_count(node, "set_motor", 2)

    @staticmethod
    def set_motor_servo(compiler, node):
        # Stub: accepted by the language, intentionally emits no runtime bytecode.
        compiler.validate_argument_count(node, "set_motor_servo", 3)
