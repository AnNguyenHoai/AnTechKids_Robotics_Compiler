# Robot Language

## Overview

Robot Language is the core language specification and build system for the Robot Development Platform.

... (các phần hiện có giữ nguyên) ...

## Standard Robot API

The Standard Robot API is the official programming interface for the Robot Development Platform. All frontends (RoboSim, Blockly, Scratch, etc.) must generate this API, and all compiler implementations must consume only this API.

### Package Structure
robot/
├── init.py # Package initializer, exports all public APIs
├── motion.py # Motion control (forward, backward, left, right, stop)
└── timing.py # Timing control (wait)

text

### Usage

```python
# Import all APIs
from robot import *

# Motion control
forward(60)      # Move forward at 60% speed
backward(40)     # Move backward at 40% speed
left(30)         # Turn left at 30% speed
right(30)        # Turn right at 30% speed
stop()           # Stop all motion

# Timing control
wait(1000)       # Wait 1000 milliseconds (1 second)
API Reference
Motion API
Function	Arguments	Description
forward(speed)	speed: int	Move robot forward
backward(speed)	speed: int	Move robot backward
left(speed)	speed: int	Turn robot left
right(speed)	speed: int	Turn robot right
stop()	None	Stop all motion
Timing API
Function	Arguments	Description
wait(milliseconds)	milliseconds: int	Blocking delay in milliseconds
Architecture Flow
text
Frontend (RoboSim, Blockly, Scratch, etc.)
        │
        ▼
Standard Robot API  ←── This package defines the API
        │
        ▼
Compiler (robot-compiler)
        │
        ▼
Bytecode
        │
        ▼
VM (robot-platform)
        │
        ▼
RobotAPI (Hardware Abstraction)
        │
        ▼
Hardware (ESP32, Arduino, etc.)
Important Notes
Frontend Independence: Any frontend can generate Standard Robot API calls.

Compiler Independence: The compiler only sees the Standard Robot API, not the original frontend.

Hardware Independence: The same API works for all supported hardware platforms.

Unit: wait() accepts milliseconds only. Frontends must convert seconds to milliseconds.

Stub Implementation: The API functions are stub implementations. The compiler replaces them with bytecode.

Examples
Example 1: Move Forward for 2 Seconds
python
from robot import *

forward(80)
wait(2000)      # 2 seconds
stop()
Example 2: Turn Left
python
from robot import *

left(50)
wait(1000)
stop()
Example 3: Sequence of Moves
python
from robot import *

forward(60)
wait(500)
right(40)
wait(500)
forward(60)
wait(1000)
stop()
Testing
To run the tests for the Standard Robot API:

bash
cd robot-language
python -m unittest discover -s tests -p "test_*.py"
Expected output: OK (all tests pass).

text

---

### Hướng dẫn áp dụng

1. **Tạo các file** theo đúng đường dẫn trong `robot-language`.
2. **Đảm bảo** thư mục `robot-language/robot` và `robot-language/tests` tồn tại.
3. **Chạy test** từ thư mục gốc hoặc từ `robot-language`:
   ```bash
   cd robot-language
   python -m unittest discover -s tests -p "test_*.py"