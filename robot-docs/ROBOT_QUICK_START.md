# Robot Quick Start

This guide shows how to compile and execute a RoboSim-generated Python program on the physical robot.

## Prerequisites

- ESP32 robot with motors connected
- USB cable
- PlatformIO installed (`pip install platformio` or use Arduino IDE)
- Python 3.8+ with required packages (click, pyyaml, pyserial)

## Steps

### 1. Prepare your RoboSim program

Place your RoboSim-generated Python file, e.g., `my_robot.py`, in the repository.

Example content:
```python
import rcu
import _thread

def task1():
    rcu.SetMoveRunSecond("forward", 50, 2)

_thread.start_new_thread(task1, ())
while 1:
    pass
2. Build the program
Use the physical build script (rewrite + compile + firmware):

bash
python tools/build_physical.py --input my_robot.py
Or manually:

2a. Rewrite RoboSim to Standard Robot API
bash
python tools/rewrite.py --input my_robot.py --output my_robot.rewrite.py
2b. Compile to C++ header
bash
python tools/compile.py --input my_robot.rewrite.py --output program.h
2c. Copy header to firmware project
bash
cp program.h robot-platform/main/src/Application/generated_program.h
2d. Build firmware
bash
pio run -d robot-platform
3. Flash the firmware to ESP32
Connect the ESP32 via USB, then:

bash
pio run -t upload -d robot-platform --upload-port COMx
Replace COMx with your serial port (e.g., COM5 on Windows, /dev/ttyUSB0 on Linux).

4. Observe serial output
Open serial monitor:

bash
pio device monitor -b 115200 -p COMx
You should see boot logs and motor commands. The robot should move according to your program.

Troubleshooting
Serial port not found: Check which port is used by ESP32 in Device Manager or ls /dev/tty*.

Compilation errors: Ensure your program uses only supported RoboSim APIs.

No movement: Verify motor wiring and power.