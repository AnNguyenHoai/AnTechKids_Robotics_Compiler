import ast
from frontend.mapping import ROBOSIM_API

class RoboSimTransformer(ast.NodeTransformer):

    def visit_Call(self, node):
        self.generic_visit(node)

        # rcu.SetMoveRun(direction, speed)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "SetMoveRun"
        ):
            direction = node.args[0].value
            speed = node.args[1]
            return ast.Call(
                func=ast.Name(
                    id=ROBOSIM_API[direction],
                    ctx=ast.Load()
                ),
                args=[speed],
                keywords=[]
            )

        # rcu.SetMoveStop()
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "SetMoveStop"
        ):
            return ast.Call(
                func=ast.Name(
                    id="stop",
                    ctx=ast.Load()
                ),
                args=[],
                keywords=[]
            )

        # rcu.SetWaitForTime(ms)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "SetWaitForTime"
        ):
            return ast.Call(
                func=ast.Name(
                    id="wait",
                    ctx=ast.Load()
                ),
                args=[node.args[0]],
                keywords=[]
            )

        return node

    def visit_Expr(self, node):
        # rcu.SetMoveRunSecond(direction, speed, seconds)
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "SetMoveRunSecond"
        ):
            call = node.value
            direction = call.args[0].value
            speed = call.args[1]
            seconds = call.args[2]

            # Chuyển đổi giây sang milliseconds: seconds * 1000
            wait_arg = ast.BinOp(
                left=seconds,
                op=ast.Mult(),
                right=ast.Constant(value=1000)
            )

            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Name(
                            id=ROBOSIM_API[direction],
                            ctx=ast.Load()
                        ),
                        args=[speed],
                        keywords=[]
                    )
                ),
                ast.Expr(
                    value=ast.Call(
                        func=ast.Name(
                            id="wait",
                            ctx=ast.Load()
                        ),
                        args=[wait_arg],
                        keywords=[]
                    )
                ),
                ast.Expr(
                    value=ast.Call(
                        func=ast.Name(
                            id="stop",
                            ctx=ast.Load()
                        ),
                        args=[],
                        keywords=[]
                    )
                )
            ]

        return self.generic_visit(node)