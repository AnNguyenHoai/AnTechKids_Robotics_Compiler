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
#### `void line_intersection_stop(int speed, int type)`
- Stop at line intersection

### Peripheral
#### `void set_mp3_play(int index)`
- Play MP3 track (adapted to active buzzer beep)


## Implementation
The RobotAPI is implemented in `robot-platform/main/src/Services/Robot/RobotAPI.cpp`.
It maps VM calls to hardware drivers (Motors, Sensors, etc.).
