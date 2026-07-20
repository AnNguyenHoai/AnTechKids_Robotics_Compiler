import ast
from frontend.mapping import ROBOSIM_API

class RoboSimTransformer(ast.NodeTransformer):

    def visit_Call(self, node):

        self.generic_visit(node)

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
        #
        # rcu.SetMoveStop()
        #
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
        #
        # rcu.SetWaitForTime(...)
        #
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "SetWaitForTime"
        ):

            return ast.Call(

                func=ast.Name(
                    id="wait",
                    ctx=ast.Load()
                ),

                args=[
                    node.args[0]
                ],

                keywords=[]
            )     
        return node


    def visit_Expr(self, node):

        #
        # Chỉ xử lý SetMoveRunSecond trước
        #
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "SetMoveRunSecond"
        ):

            call = node.value

            direction = call.args[0].value
            speed = call.args[1]
            seconds = call.args[2]

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
                        args=[seconds],
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

        #
        # Những Expr khác mới đi xuống transform
        #
        return self.generic_visit(node)
