import ast
from frontend.mapping import ROBOSIM_API, SENSOR_API_MAPPING


class RoboSimTransformer(ast.NodeTransformer):
    """Transform RoboSim AST to Standard Robot API AST."""

    # ----------------------------------------------------------------------
    # Remove 'import rcu' and 'import _thread' statements
    # ----------------------------------------------------------------------

    def visit_Import(self, node):
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
    # Transform all calls, including nested ones
    # ----------------------------------------------------------------------

    def visit_Call(self, node):
        # First, visit child nodes to transform any nested RoboSim calls
        node = self.generic_visit(node)

        # Check if this is a RoboSim sensor API call
        if (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'rcu'):
            attr = node.func.attr
            mapping = SENSOR_API_MAPPING.get(attr)
            if mapping:
                return self._transform_sensor_call(node, attr, mapping)

        return node

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------

    def _handle_move_run_second(self, call):
        direction = call.args[0].value
        speed = call.args[1]
        seconds = call.args[2]

        if isinstance(seconds, ast.Constant) and isinstance(seconds.value, (int, float)):
            ms = int(seconds.value * 1000)
            wait_arg = ast.Constant(value=ms)
        else:
            wait_arg = ast.BinOp(left=seconds, op=ast.Mult(), right=ast.Constant(value=1000))

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
        func = call.args[0]
        return ast.Expr(
            ast.Call(
                func=func,
                args=[],
                keywords=[]
            )
        )

    def _transform_sensor_call(self, node, attr, mapping):
        """Transform a RoboSim sensor call based on mapping."""
        expected = mapping["expected_args"]
        actual = len(node.args)
        if actual != expected:
            raise SyntaxError(
                f"RoboSim API '{attr}()' expects exactly {expected} argument(s), got {actual}"
            )

        target_name = mapping["target"]
        arg_indices = mapping["arg_indices"]
        args = [node.args[i] for i in arg_indices if i < len(node.args)]

        return ast.Call(
            func=ast.Name(id=target_name, ctx=ast.Load()),
            args=args,
            keywords=[]
        )