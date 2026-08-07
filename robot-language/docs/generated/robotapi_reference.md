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

#### `void set_motor_speed(int left_speed, int right_speed)`
- Set motor speeds independently

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

#### `void get_trace_value(int port, int channel)`
- Get trace sensor value (0/50/100 based on line detection)

#### `void get_trace_state(int port, int channel)`
- Get trace sensor state (boolean)

#### `void get_trace_raw(int port)`
- Get raw bitmask of all 3 trace sensors

### Servo
#### `void set_servo(int port, int angle)`
- Set servo angle

### Led
#### `void set_3c_led(int port, int state)`
- Set 3-color LED state

#### `void set_light_sensor_led(int port, int state)`
- Set light sensor LED state

### Motor
#### `void set_motor_straight_angle(int left_port, int right_port, int speed, int angle)`
- Set motor straight angle

### Line
#### `void line_basis(int speed)`
- Basic line following step (adjust motors based on sensor mask)

#### `void line_follow(int speed)`
- Follow line continuously until lost

#### `void line_stop()`
- Stop line following (stop motors)

#### `void line_intersection_stop(int speed, int type)`
- Stop at line intersection

#### `void line_turn_encounterline(int speed, int angle, int direction)`
- Turn until line encountered

#### `void line_for_bmp(int speed, int degree)`
- Follow line for a given degree (time-based approximation)

### Peripheral
#### `void set_mp3_play(int index)`
- Play MP3 track (adapted to active buzzer beep)


## Implementation
The RobotAPI is implemented in `robot-platform/main/src/Services/Robot/RobotAPI.cpp`.
It maps VM calls to hardware drivers (Motors, Sensors, etc.).
