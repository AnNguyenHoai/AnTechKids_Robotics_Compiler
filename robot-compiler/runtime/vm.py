# runtime/vm.py
from typing import Optional
from .program import RuntimeProgram
from .engine import ExecutionEngine
from .dispatcher import Dispatcher
from .robot import RobotRuntime
from .hardware import MockHardware
from .context import ExecutionState

class VirtualMachine:
    def __init__(self, hardware=None):
        if hardware is None:
            hardware = MockHardware()
        self.hardware = hardware
        self.robot = RobotRuntime(hardware)
        self.engine = ExecutionEngine()
        self.dispatcher = Dispatcher()
        self.state = ExecutionState.CREATED

    def load(self, program: RuntimeProgram):
        self.engine.load(program)
        self.state = ExecutionState.LOADED

    def step(self):
        if self.state == ExecutionState.FINISHED:
            raise RuntimeError("VM already finished")
        if self.state not in (ExecutionState.LOADED, ExecutionState.RUNNING, ExecutionState.PAUSED):
            raise RuntimeError(f"VM in invalid state: {self.state}")

        if not self.engine.iterator.has_next():
            self.state = ExecutionState.FINISHED
            self.engine.context.state = ExecutionState.FINISHED
            return

        ins = self.engine.iterator.current()
        if ins is None:
            self.state = ExecutionState.FINISHED
            self.engine.context.state = ExecutionState.FINISHED
            return

        # Dispatch using robot instead of api
        self.dispatcher.dispatch(ins, self.engine, self.robot)

        # Sync iterator with program_counter
        self.engine.iterator.seek(self.engine.context.program_counter)

    def run(self):
        self.state = ExecutionState.RUNNING
        self.engine.context.state = ExecutionState.RUNNING
        while self.state == ExecutionState.RUNNING:
            self.step()
            if self.state == ExecutionState.FINISHED:
                break

    def stop(self):
        self.state = ExecutionState.STOPPED
        self.engine.context.state = ExecutionState.STOPPED

    def reset(self):
        self.engine = ExecutionEngine()
        self.state = ExecutionState.CREATED

    def get_state(self):
        return self.state