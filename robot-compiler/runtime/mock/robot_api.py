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

    # --- Added for sensors ---
    def read_ultrasonic(self):
        print("[MockRobot] Read ultrasonic")
        return 50

    def read_touch(self, port):
        print(f"[MockRobot] Read touch port {port}")
        return 0

    def read_light(self, channel):
        print(f"[MockRobot] Read light channel {channel}")
        return 512

    def read_line(self, channel):
        print(f"[MockRobot] Read line channel {channel}")
        return 0

    def read_color(self):
        print("[MockRobot] Read color")
        return 0

    # --- Added for LED/MP3 ---
    def set_led(self, port, state):
        print(f"[MockRobot] Set LED port {port} state {state}")
        self.output.append(("set_led", port, state))

    def set_mp3_play(self, index):
        print(f"[MockRobot] Play MP3 index {index}")
        self.output.append(("mp3", index))

    # --- Added for motor speed ---
    def set_motor_speed(self, left, right):
        print(f"[MockRobot] Set motor speed left={left} right={right}")
        self.output.append(("set_motor_speed", left, right))