# RobotAPI Reference (C++)

The RobotAPI is the hardware abstraction layer. All robot hardware access goes through this API.

## Functions

### Motion
#### `void forward(int speed)`
- Move robot forward

#### `void backward(int speed)`
- Move robot backward

#### `void turn_left(int speed)`
- Rotate robot left

#### `void turn_right(int speed)`
- Rotate robot right

### System
#### `void wait(int milliseconds)`
- Wait milliseconds

#### `void stop()`
- Stop robot

### Sensor
#### `void read_ultrasonic()`
- Read ultrasonic distance in cm

#### `void read_touch(int port)`
- Read touch sensor state (0/1)

#### `void read_light(int channel)`
- Read light sensor raw value (0-1023)

#### `void read_color()`
- Read color sensor (placeholder)

#### `void read_line(int channel)`
- Read line sensor (0=white, 1=dark)


## Implementation
The RobotAPI is implemented in `robot-platform/main/src/Services/Robot/RobotAPI.cpp`.
It maps VM calls to hardware drivers (Motors, Sensors, etc.).
