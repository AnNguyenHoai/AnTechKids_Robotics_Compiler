import ast
from frontend.mapping import ROBOSIM_API


class RoboSimTransformer(ast.NodeTransformer):
    """Transform RoboSim AST to Standard Robot API AST."""

    # ----------------------------------------------------------------------
    # Remove 'import rcu' and 'import _thread' statements
    # ----------------------------------------------------------------------

    def visit_Import(self, node):
        # Keep only imports that are not rcu or _thread
        new_names = [alias for alias in node.names if alias.name not in ('rcu', '_thread')]
        if new_names:
            node.names = new_names
            return node
        return None

    def visit_ImportFrom(self, node):
        if node.module in ('rcu', '_thread'):
            return None
        return node

    # ----------------------------------------------------------------------
    # Transform expressions: function calls
    # ----------------------------------------------------------------------

    def visit_Expr(self, node):
        self.generic_visit(node)

        # Handle rcu.SetMoveRunSecond -> forward, wait, stop
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMoveRunSecond"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_move_run_second(node.value)

        # Handle rcu.SetMoveRun -> forward/backward/turn_left/turn_right
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMoveRun"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return self._handle_move_run(node.value)

        # Handle rcu.SetMoveStop -> stop()
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetMoveStop"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            return ast.Expr(
                ast.Call(
                    func=ast.Name(id="stop", ctx=ast.Load()),
                    args=[],
                    keywords=[]
                )
            )

        # Handle rcu.SetWaitForTime -> wait(milliseconds)
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "SetWaitForTime"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "rcu"):
            arg = node.value.args[0]
            return ast.Expr(
                ast.Call(
                    func=ast.Name(id="wait", ctx=ast.Load()),
                    args=[arg],
                    keywords=[]
                )
            )

        # Handle _thread.start_new_thread(func, ()) -> func()
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == '_thread'
                and node.value.func.attr == 'start_new_thread'):
            return self._handle_thread_start(node.value)

        return node

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------

    def _handle_move_run_second(self, call):
        """Transform rcu.SetMoveRunSecond(direction, speed, seconds) into:
           forward(speed); wait(seconds*1000); stop()
        """
        direction = call.args[0].value
        speed = call.args[1]
        seconds = call.args[2]

        # Convert seconds to milliseconds
        if isinstance(seconds, ast.Constant) and isinstance(seconds.value, (int, float)):
            ms = int(seconds.value * 1000)
            wait_arg = ast.Constant(value=ms)
        else:
            wait_arg = ast.BinOp(left=seconds, op=ast.Mult(), right=ast.Constant(value=1000))

        # Build three statements
        forward_call = ast.Call(
            func=ast.Name(id=ROBOSIM_API.get(direction, direction), ctx=ast.Load()),
            args=[speed],
            keywords=[]
        )
        wait_call = ast.Call(
            func=ast.Name(id="wait", ctx=ast.Load()),
            args=[wait_arg],
            keywords=[]
        )
        stop_call = ast.Call(
            func=ast.Name(id="stop", ctx=ast.Load()),
            args=[],
            keywords=[]
        )

        return [
            ast.Expr(forward_call),
            ast.Expr(wait_call),
            ast.Expr(stop_call)
        ]

    def _handle_move_run(self, call):
        """Transform rcu.SetMoveRun(direction, speed) into:
           forward(speed) / backward(speed) / turn_left(speed) / turn_right(speed)
        """
        direction = call.args[0].value
        speed = call.args[1]
        func_name = ROBOSIM_API.get(direction, direction)
        return ast.Expr(
            ast.Call(
                func=ast.Name(id=func_name, ctx=ast.Load()),
                args=[speed],
                keywords=[]
            )
        )

    def _handle_thread_start(self, call):
        """Transform _thread.start_new_thread(func, ()) into func()"""
        func = call.args[0]
        return ast.Expr(
            ast.Call(
                func=func,
                args=[],
                keywords=[]
            )
        )