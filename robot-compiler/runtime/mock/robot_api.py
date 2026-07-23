# runtime/mock/robot_api.py
class MockRobotAPI:
    def __init__(self):
        self.output = []
        self.last_action = None

    def forward(self, speed):
        self.last_action = ("forward", speed)
        self.output.append(("forward", speed))
        print(f"[MockRobot] Forward {speed}")

    def backward(self, speed):
        self.last_action = ("backward", speed)
        self.output.append(("backward", speed))
        print(f"[MockRobot] Backward {speed}")

    def left(self, speed):
        self.last_action = ("left", speed)
        self.output.append(("left", speed))
        print(f"[MockRobot] Left {speed}")

    def right(self, speed):
        self.last_action = ("right", speed)
        self.output.append(("right", speed))
        print(f"[MockRobot] Right {speed}")

    def stop(self):
        self.last_action = ("stop",)
        self.output.append(("stop",))
        print(f"[MockRobot] Stop")

    def wait(self, ms):
        self.last_action = ("wait", ms)
        self.output.append(("wait", ms))
        print(f"[MockRobot] Wait {ms} ms")