class MotionHandler:

    @staticmethod
    def forward(compiler, node):

        index = compiler.resolve_argument(
            node.args[0]
        )
        compiler.program.emit(
            compiler.opcodes.get("Forward"),
            index
        )

    @staticmethod
    def backward(compiler, node):



        index = compiler.resolve_argument(
            node.args[0]
        )

        compiler.program.emit(
            compiler.opcodes.get("Backward"),
            index
        )

    @staticmethod
    def turn_left(compiler, node):


        index = compiler.resolve_argument(
            node.args[0]
        )

        compiler.program.emit(
            compiler.opcodes.get("TurnLeft"),
            index
        )

    @staticmethod
    def turn_right(compiler, node):

        index = compiler.resolve_argument(
            node.args[0]
        )

        compiler.program.emit(
            compiler.opcodes.get("TurnRight"),
            index
        )