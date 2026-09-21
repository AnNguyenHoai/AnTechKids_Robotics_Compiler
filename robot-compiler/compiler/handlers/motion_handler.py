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

    @staticmethod
    def set_motor_speed(compiler, node):
        compiler.validate_argument_count(node, "set_motor_speed", 2)
        left = compiler.resolve_argument(node.args[0])
        right = compiler.resolve_argument(node.args[1])
        compiler.program.emit(Opcode.SetMotorSpeed.value, left, right, 0)

    @staticmethod
    def set_move_initialize(compiler, node):
        # Stub: accepted by the language, intentionally emits no runtime bytecode.
        compiler.validate_argument_count(node, "set_move_initialize", 3)

    @staticmethod
    def set_move_run_angle(compiler, node):
        # Approximation placeholder: accepted until a real runtime lowering exists.
        # Do not emit Opcode.Nop because the physical VM does not dispatch Nop.
        compiler.validate_argument_count(node, "set_move_run_angle", 3)
