Robot Hardware Abstraction Layer (HAL) Specification
Version: 1.0
Status: Architecture Freeze
Date: 2026-08-10
Owner: Robot Platform Team

Revision History
Version	Date	Author	Changes
1.0	2026-08-10	DeepSeek	Initial release
Table of Contents
Introduction

HAL Design Philosophy

Architecture

HAL Categories

Motion HAL

Sensor HAL

Output HAL

Timing HAL

Communication HAL

Storage HAL

System HAL

Driver Model

Error Model

Versioning

Board Porting Guide
Appendix A: HAL Interface Summary
Appendix B: Driver Categories
Appendix C: Error Codes
Appendix D: Timing Rules
Appendix E: Board Capability Matrix
Appendix F: Initialization Order

Chapter 1 – Introduction
1.1 Purpose
This document defines the official Hardware Abstraction Layer (HAL) specification for the Robot Platform.

The HAL exists to decouple the Robot Platform from physical hardware.

Every supported board SHALL provide a HAL implementation that conforms to this specification.

The HAL SHALL isolate all hardware-specific implementation details.

The Runtime and RobotAPI SHALL remain completely unaware of the underlying hardware platform.

1.2 Scope
This specification covers:

HAL architecture and layers

All HAL interface categories (Motion, Sensor, Output, Timing, Communication, Storage, System)

Driver model and lifecycle

Error handling and reporting

Board porting requirements

Versioning and compatibility

It does not cover:

RobotAPI semantics (covered by ROBOT_PLATFORM_API.md)

VM or Runtime internals

Specific hardware register details

Pin numbers or GPIO assignments

Compiler or toolchain specifics

1.3 Relationship with RobotAPI
text
RobotAPI (Platform API)
        │
        ▼
    HAL (this document)
        │
        ▼
    Board Drivers
        │
        ▼
    Hardware
RobotAPI calls HAL functions to perform hardware operations. RobotAPI does not call drivers directly.

1.4 Relationship with Drivers
HAL owns the driver abstraction. Drivers implement the actual hardware control. HAL provides a unified interface to RobotAPI; drivers are platform-specific and implement the HAL interfaces.

1.5 Relationship with Runtime
The Runtime SHALL NOT call HAL directly. All hardware access goes through RobotAPI, which then calls HAL. This enforces a clean separation between execution logic and hardware control.

Chapter 2 – HAL Design Philosophy
2.1 Hardware Independence
HAL SHALL NOT expose:

Microcontroller-specific types

Register addresses

Clock frequencies

Peripheral IDs

Pin numbers

All hardware details are hidden behind driver interfaces.

2.2 Board Independence
The same HAL interface SHALL work for all supported boards. Board-specific differences are handled by the driver implementations, not by the interface.

2.3 Driver Isolation
Each hardware device SHALL have its own driver. Drivers SHALL NOT know about each other. Drivers SHALL NOT know about RobotAPI or Runtime.

2.4 Deterministic Behaviour
HAL operations SHALL be deterministic. Given the same inputs and same hardware state, the output SHALL be identical.

2.5 Minimal Surface Area
HAL SHALL expose the minimal set of operations necessary to support the Robot Platform. Unnecessary abstractions SHALL be avoided.

2.6 Replaceability
Any driver SHALL be replaceable with an alternative implementation without affecting RobotAPI or Runtime.

2.7 Testability
HAL SHALL support mock implementations for unit testing. Mock drivers SHALL be provided for each interface.

2.8 Portability
The HAL specification SHALL be implementable on any microcontroller or platform that supports C++ (or C) with standard peripherals.

Chapter 3 – Architecture
3.1 Overall Architecture
text
+-------------------+
|     Runtime       |
|  (Virtual Machine)|
+--------+----------+
         │
         ▼
+-------------------+
|    RobotAPI       |
|  (Platform API)   |
+--------+----------+
         │
         ▼
+-------------------+
|       HAL         |
| (This Specification)|
+--------+----------+
         │
         ▼
+-------------------+
|   Board Drivers   |
|  (MCU-specific)   |
+--------+----------+
         │
         ▼
+-------------------+
|     Hardware      |
| (Physical Devices)|
+-------------------+
3.2 Layer Responsibilities
Layer	Responsibility
Runtime	Executes bytecode; issues RobotAPI requests.
RobotAPI	Translates requests to HAL calls; manages platform state.
HAL	Provides abstract hardware interfaces; routes to drivers.
Board Drivers	Implement hardware-specific logic; control MCU peripherals.
Hardware	Physical devices (motors, sensors, LEDs, etc.).
3.3 Dependency Rules
Dependencies only flow downward.

RobotAPI SHALL NOT know about specific drivers.

HAL SHALL NOT know about RobotAPI or Runtime.

Drivers SHALL NOT know about RobotAPI or Runtime.

Drivers SHALL NOT know about each other.

3.4 Forbidden Dependencies
RobotAPI → Driver (direct)

Runtime → HAL

Runtime → Driver

Driver → RobotAPI

Driver → Runtime

Driver → Driver

Chapter 4 – HAL Categories
HAL interfaces are grouped into categories.

Category	Description
Motion HAL	Motor control, braking, speed, direction.
Sensor HAL	Ultrasonic, line, touch, light, color sensors.
Output HAL	LEDs, buzzer, display, servo.
Timing HAL	Delays, timers, current time, sleep.
Communication HAL	UART, I2C, SPI, CAN, BLE, WiFi, USB.
Storage HAL	Flash, EEPROM, file system, configuration storage.
System HAL	Reset, watchdog, battery, board info, power.
Chapter 5 – Motion HAL
5.1 Overview
The Motion HAL abstracts motor control. All speed values are signed integers in the range -100 to +100, where sign indicates direction and magnitude indicates duty cycle (percentage).

5.2 Interface: setMotorSpeed
Purpose: Set speed of left and right motors.

Signature:

cpp
void setMotorSpeed(int left, int right);
Parameters:

Name	Type	Range	Description
left	int	-100..100	Left motor speed
right	int	-100..100	Right motor speed
Description: Sets both motors to the specified speeds. Negative values reverse direction.

Failure Conditions: None; values are clamped to range.

Timing: Immediate; non-blocking.

State Change: Motor speeds updated.

5.3 Interface: stopMotors
Purpose: Immediately stop both motors.

Signature:

cpp
void stopMotors();
Parameters: None.

Description: Sets both motors to 0.

Timing: Immediate.

5.4 Interface: brakeMotors
Purpose: Apply active braking to both motors (if supported).

Signature:

cpp
void brakeMotors();
Parameters: None.

Description: Some motor drivers support braking by shorting motor terminals. If not supported, this SHALL behave like stopMotors().

Timing: Immediate.

5.5 Interface: getMotorSpeed
Purpose: Read current motor speeds (optional).

Signature:

cpp
void getMotorSpeed(int& left, int& right) const;
Parameters:

Name	Type	Description
left	int&	Output: left motor speed
right	int&	Output: right motor speed
Description: Reads the last set speed values. This may not reflect actual hardware if drivers are not read-back capable.

Timing: Non-blocking.

5.6 Future Interfaces
Interface	Description
setMotorDirection	Set direction only (for stepper motors)
setMotorPWM	Set PWM duty directly (0–255)
enableMotor / disableMotor	Enable/disable motor driver
setServoAngle	Set servo angle (if servo is part of motion subsystem)
Chapter 6 – Sensor HAL
6.1 Overview
Sensor HAL provides read interfaces for all sensors. All sensor reads are non-blocking and return immediately.

6.2 Interface: readUltrasonic
Purpose: Read distance from ultrasonic sensor (HC-SR04 or similar).

Signature:

cpp
int16_t readUltrasonic();
Parameters: None.

Return: Distance in centimeters (0–400) or -1 on timeout/error.

Description: Triggers an ultrasonic pulse and measures echo duration. Returns distance in cm.

Timing: Non-blocking; may take up to a few milliseconds.

6.3 Interface: readLineSensor
Purpose: Read digital line sensor (TCRT5000 or similar).

Signature:

cpp
bool readLineSensor(int channel);
Parameters:

Name	Type	Description
channel	int	0 = Left, 1 = Center, 2 = Right
Return: true if line (black) detected, false otherwise.

Description: Reads the digital output of a line sensor. The interpretation (HIGH = line) is board-dependent; the interface returns normalized result.

Timing: Instant.

6.4 Interface: readTouch
Purpose: Read touch sensor state.

Signature:

cpp
bool readTouch(int port);
Parameters:

Name	Type	Description
port	int	Touch sensor port number
Return: true if pressed, false otherwise.

Description: Reads touch sensor state with debouncing.

Timing: Instant.

6.5 Interface: readLight
Purpose: Read analog light sensor (photoresistor, photodiode).

Signature:

cpp
int16_t readLight(int channel);
Parameters:

Name	Type	Description
channel	int	Sensor channel (typically 0)
Return: Raw ADC value (0–4095 or 0–1023 depending on resolution).

Description: Reads analog light level.

Timing: Non-blocking.

6.6 Interface: readColor
Purpose: Read color sensor (placeholder).

Signature:

cpp
int16_t readColor();
Return: Color ID (0 = unknown, 1 = red, 2 = green, 3 = blue, etc.).

Description: Placeholder; may be implemented with a color sensor.

Timing: Non-blocking.

6.7 Future Interfaces
Interface	Description
readIMU	Read accelerometer/gyroscope
readEncoder	Read encoder count
readGyroscope	Read angular velocity
readCamera	Capture image frame
Chapter 7 – Output HAL
7.1 Overview
Output HAL controls actuators and indicators: LEDs, buzzers, displays.

7.2 Interface: setLED
Purpose: Turn an LED on or off.

Signature:

cpp
void setLED(int index, bool state);
Parameters:

Name	Type	Description
index	int	LED index (0..N-1)
state	bool	true = on, false = off
Description: Sets the specified LED to on/off.

Timing: Immediate.

7.3 Interface: setBuzzer
Purpose: Turn active buzzer on/off.

Signature:

cpp
void setBuzzer(bool state);
Parameters:

Name	Type	Description
state	bool	true = on, false = off
Description: Controls the active buzzer.

Timing: Immediate.

7.4 Interface: setDisplay
Purpose: Display a string (reserved).

Signature:

cpp
void setDisplay(const char* text);
Parameters:

Name	Type	Description
text	const char*	Null-terminated string
Description: Displays text on a character or graphical display.

Future: May be extended with position, color, etc.

7.5 Future Interfaces
Interface	Description
setRGB	Set RGB color for addressable LEDs
setServo	Set servo angle
setDisplayPosition	Set display cursor
clearDisplay	Clear display
Chapter 8 – Timing HAL
8.1 Overview
Timing HAL provides time-related functions: delays, timers, and current time.

8.2 Interface: delayMs
Purpose: Blocking delay in milliseconds.

Signature:

cpp
void delayMs(uint32_t ms);
Parameters:

Name	Type	Description
ms	uint32_t	Delay in milliseconds
Description: Blocks for at least ms milliseconds.

Timing: Blocking.

8.3 Interface: delayUs
Purpose: Blocking delay in microseconds.

Signature:

cpp
void delayUs(uint32_t us);
Parameters:

Name	Type	Description
us	uint32_t	Delay in microseconds
Description: Blocks for at least us microseconds.

Timing: Blocking.

8.4 Interface: millis
Purpose: Get current time in milliseconds.

Signature:

cpp
uint32_t millis();
Return: Milliseconds since system boot.

Description: Returns the current uptime.

Timing: Non-blocking.

8.5 Interface: micros
Purpose: Get current time in microseconds.

Signature:

cpp
uint32_t micros();
Return: Microseconds since system boot.

Description: Returns the current uptime with microsecond precision.

Timing: Non-blocking.

8.6 Interface: setTimer
Purpose: Set a timer callback (future).

Signature:

cpp
void setTimer(uint32_t interval, void (*callback)(void*), void* arg);
Parameters:

Name	Type	Description
interval	uint32_t	Interval in milliseconds
callback	function pointer	Callback function
arg	void*	Argument passed to callback
Description: Sets a timer that calls the callback repeatedly at the specified interval.

Future: Not required in version 1.0.

8.7 Interface: sleep
Purpose: Low-power sleep for a given duration (future).

Signature:

cpp
void sleep(uint32_t ms);
Description: Puts the MCU into a low-power state for ms milliseconds, then resumes.

Future: Not required in version 1.0.

Chapter 9 – Communication HAL
9.1 Overview
Communication HAL abstracts serial and bus communication. All interfaces are non-blocking and use callbacks or polling.

9.2 Interface: uartSend
Purpose: Send data over UART.

Signature:

cpp
void uartSend(uint8_t* data, size_t length);
Parameters:

Name	Type	Description
data	uint8_t*	Buffer to send
length	size_t	Number of bytes
Description: Sends data over the default UART (typically for debug output).

Timing: Non-blocking; may buffer data.

9.3 Interface: uartReceive
Purpose: Receive data over UART.

Signature:

cpp
int uartReceive(uint8_t* buffer, size_t maxLength);
Return: Number of bytes received, or -1 on error.

Description: Reads available data from UART into the buffer.

Timing: Non-blocking.

9.4 Interface: i2cWrite
Purpose: Write data over I2C.

Signature:

cpp
bool i2cWrite(uint8_t address, const uint8_t* data, size_t length);
Return: true on success, false on failure.

Description: Writes data to an I2C device.

Timing: Non-blocking; may use interrupts.

9.5 Interface: i2cRead
Purpose: Read data over I2C.

Signature:

cpp
bool i2cRead(uint8_t address, uint8_t* buffer, size_t length);
Return: true on success, false on failure.

Description: Reads data from an I2C device.

Timing: Non-blocking.

9.6 Interface: spiTransfer
Purpose: Perform SPI transfer.

Signature:

cpp
bool spiTransfer(const uint8_t* tx, uint8_t* rx, size_t length);
Return: true on success, false on failure.

Description: Transmits and receives data over SPI.

Timing: Non-blocking.

9.7 Interface: bleSend
Purpose: Send data over BLE (future).

Signature:

cpp
void bleSend(const uint8_t* data, size_t length);
Description: Sends data via Bluetooth Low Energy.

Future: Not required in version 1.0.

9.8 Interface: wifiSend
Purpose: Send data over WiFi (future).

Signature:

cpp
void wifiSend(const uint8_t* data, size_t length);
Description: Sends data via WiFi.

Future: Not required in version 1.0.

9.9 Interface: usbSend
Purpose: Send data over USB (future).

Signature:

cpp
void usbSend(const uint8_t* data, size_t length);
Description: Sends data via USB.

Future: Not required in version 1.0.

Chapter 10 – Storage HAL
10.1 Overview
Storage HAL abstracts persistent storage: flash, EEPROM, file systems.

10.2 Interface: flashRead
Purpose: Read from flash memory.

Signature:

cpp
bool flashRead(uint32_t address, uint8_t* buffer, size_t length);
Return: true on success, false on failure.

Description: Reads data from flash memory.

Timing: Non-blocking.

10.3 Interface: flashWrite
Purpose: Write to flash memory.

Signature:

cpp
bool flashWrite(uint32_t address, const uint8_t* data, size_t length);
Return: true on success, false on failure.

Description: Writes data to flash memory.

Timing: Non-blocking; may be slower.

10.4 Interface: flashErase
Purpose: Erase a flash sector.

Signature:

cpp
bool flashErase(uint32_t address, size_t size);
Return: true on success, false on failure.

Description: Erases flash memory.

Timing: Blocking (may take time).

10.5 Interface: eepromRead
Purpose: Read from EEPROM.

Signature:

cpp
bool eepromRead(uint16_t address, uint8_t* buffer, size_t length);
Return: true on success, false on failure.

Description: Reads data from EEPROM.

10.6 Interface: eepromWrite
Purpose: Write to EEPROM.

Signature:

cpp
bool eepromWrite(uint16_t address, const uint8_t* data, size_t length);
Return: true on success, false on failure.

Description: Writes data to EEPROM.

10.7 Interface: configSave
Purpose: Save configuration to persistent storage.

Signature:

cpp
bool configSave(const char* key, const uint8_t* data, size_t length);
Return: true on success, false on failure.

Description: Stores a configuration blob.

10.8 Interface: configLoad
Purpose: Load configuration from persistent storage.

Signature:

cpp
bool configLoad(const char* key, uint8_t* buffer, size_t* length);
Return: true on success, false on failure.

Description: Reads a configuration blob.

Chapter 11 – System HAL
11.1 Overview
System HAL provides board-level operations: reset, power, watchdog, board info.

11.2 Interface: systemReset
Purpose: Perform a system reset.

Signature:

cpp
void systemReset();
Description: Resets the entire system.

Timing: Immediate.

11.3 Interface: watchdogReset
Purpose: Reset the watchdog timer.

Signature:

cpp
void watchdogReset();
Description: Feeds the watchdog to prevent a reset.

Timing: Immediate.

11.4 Interface: watchdogEnable
Purpose: Enable the watchdog timer.

Signature:

cpp
void watchdogEnable(uint32_t timeoutMs);
Parameters:

Name	Type	Description
timeoutMs	uint32_t	Timeout in milliseconds
Description: Enables the watchdog with the specified timeout.

11.5 Interface: batteryVoltage
Purpose: Read battery voltage.

Signature:

cpp
float batteryVoltage();
Return: Battery voltage in volts.

Description: Reads the battery voltage.

11.6 Interface: boardInfo
Purpose: Get board identification.

Signature:

cpp
const char* boardInfo();
Return: Board name string.

11.7 Interface: firmwareVersion
Purpose: Get firmware version.

Signature:

cpp
const char* firmwareVersion();
Return: Version string.

11.8 Interface: powerOff
Purpose: Power off the system (future).

Signature:

cpp
void powerOff();
Description: Shuts down the system.

Chapter 12 – Driver Model
12.1 Overview
HAL drivers implement the interfaces defined in this specification. Each driver SHALL manage one hardware device.

12.2 Driver Registration
Drivers SHALL be registered with the HAL layer during system initialization. Registration SHALL occur before any hardware operations.

12.3 Initialization
Every driver SHALL provide an init() function that:

Configures hardware (GPIO, clocks, etc.)

Sets initial state

Returns success/failure

Signature:

cpp
bool init();
Return: true on success, false on failure.

12.4 Startup
After initialization, drivers SHALL be started. The startup function SHALL:

Enable hardware

Prepare for normal operation

Signature:

cpp
void start();
12.5 Shutdown
Drivers SHALL support shutdown to release hardware resources.

Signature:

cpp
void shutdown();
12.6 Error Handling
Drivers SHALL detect hardware errors and report them via the error model (Chapter 13). Errors SHALL be logged and returned to RobotAPI.

12.7 Ownership
HAL owns all drivers.

Drivers own their hardware resources (GPIO, timers, interrupts).

Drivers SHALL NOT share resources without coordination.

12.8 Lifetime
Drivers SHALL follow this lifecycle:

text
Created
   │
   ▼
Initialized (init)
   │
   ▼
Started (start)
   │
   ▼
Running (normal operation)
   │
   ▼
Shutdown (shutdown)
   │
   ▼
Destroyed
Chapter 13 – Error Model
13.1 Error Categories
Category	Description
Success	Operation completed successfully.
Busy	Hardware is busy and cannot accept the operation.
Timeout	Operation timed out.
Unsupported	Operation is not supported by this hardware.
Invalid Parameter	One or more parameters are invalid.
Hardware Failure	Hardware malfunction.
Initialization Failure	Driver failed to initialize.
Recoverable Error	Error that can be resolved by retrying.
Fatal Error	Unrecoverable error; system may require reset.
13.2 Error Reporting
All HAL functions SHALL return a boolean true for success, false for failure, and SHALL provide a way to retrieve detailed error information.

Error Retrieval:

cpp
int getLastError();  // returns error code
const char* getErrorString(); // returns human-readable message
13.3 Error Codes
Code	Name	Description
0	HAL_OK	Success
1	HAL_BUSY	Device busy
2	HAL_TIMEOUT	Operation timed out
3	HAL_UNSUPPORTED	Operation not supported
4	HAL_INVALID_PARAM	Invalid parameter
5	HAL_HARDWARE_FAILURE	Hardware failure
6	HAL_INIT_FAILURE	Initialization failed
13.4 Recovery
Busy: Retry after a short delay.

Timeout: Increase timeout or check hardware connection.

Invalid Parameter: Correct the parameter.

Hardware Failure: Reset the driver or system.

Chapter 14 – Versioning
14.1 HAL Version
The HAL version SHALL be independent of RobotAPI and VM versions.

14.2 Version Number
MAJOR.MINOR.PATCH

MAJOR: Breaking interface changes

MINOR: New interfaces added

PATCH: Bug fixes, no interface changes

14.3 Compatibility Rules
Same major version: backward compatible.

Different major version: not guaranteed compatible.

New interfaces may be added in minor versions.

14.4 Board Profiles
Each board SHALL provide a profile indicating which HAL interfaces are supported. Unsupported interfaces SHALL return HAL_UNSUPPORTED.

Chapter 15 – Board Porting Guide
15.1 Minimum Implementation
To port the HAL to a new board, the following interfaces must be implemented:

Motion HAL: setMotorSpeed, stopMotors

Timing HAL: delayMs, delayUs, millis, micros

Output HAL: setLED, setBuzzer (if hardware present)

Sensor HAL: readUltrasonic, readLineSensor, readTouch, readLight (if sensors present)

System HAL: systemReset, boardInfo

15.2 Optional Interfaces
All other interfaces are optional. If not supported, they SHALL return HAL_UNSUPPORTED or appropriate error.

15.3 Initialization Order
System HAL (board identification, reset)

Timing HAL (initialize timers)

Motion HAL (configure motor pins)

Output HAL (configure LEDs, buzzer)

Sensor HAL (configure sensor pins)

Communication HAL (configure UART, I2C, SPI)

Storage HAL (initialize flash/EEPROM)

15.4 Validation Checklist
□ All required interfaces implemented.
□ All functions return correct error codes.
□ Timing functions are accurate.
□ Motor control works with correct direction.
□ Sensors report correct values.
□ LEDs and buzzer respond correctly.
15.5 Certification Checklist
□ All HAL interfaces documented.
□ Full test suite passes.
□ No hardware-specific types exposed.
□ Error handling complete.
Appendix A – HAL Interface Summary
Category	Interface	Signature	Description
Motion	setMotorSpeed	void setMotorSpeed(int, int)	Set motor speeds
Motion	stopMotors	void stopMotors()	Stop motors
Motion	brakeMotors	void brakeMotors()	Brake motors
Motion	getMotorSpeed	void getMotorSpeed(int&, int&)	Read speeds
Sensor	readUltrasonic	int16_t readUltrasonic()	Read distance
Sensor	readLineSensor	bool readLineSensor(int)	Line detect
Sensor	readTouch	bool readTouch(int)	Touch state
Sensor	readLight	int16_t readLight(int)	Light value
Sensor	readColor	int16_t readColor()	Color
Output	setLED	void setLED(int, bool)	LED on/off
Output	setBuzzer	void setBuzzer(bool)	Buzzer on/off
Output	setDisplay	void setDisplay(const char*)	Display text
Timing	delayMs	void delayMs(uint32_t)	Delay ms
Timing	delayUs	void delayUs(uint32_t)	Delay us
Timing	millis	uint32_t millis()	Current time ms
Timing	micros	uint32_t micros()	Current time us
Communication	uartSend	void uartSend(uint8_t*, size_t)	UART send
Communication	uartReceive	int uartReceive(uint8_t*, size_t)	UART receive
Communication	i2cWrite	bool i2cWrite(uint8_t, const uint8_t*, size_t)	I2C write
Communication	i2cRead	bool i2cRead(uint8_t, uint8_t*, size_t)	I2C read
Communication	spiTransfer	bool spiTransfer(const uint8_t*, uint8_t*, size_t)	SPI transfer
Storage	flashRead	bool flashRead(uint32_t, uint8_t*, size_t)	Flash read
Storage	flashWrite	bool flashWrite(uint32_t, const uint8_t*, size_t)	Flash write
Storage	flashErase	bool flashErase(uint32_t, size_t)	Flash erase
Storage	eepromRead	bool eepromRead(uint16_t, uint8_t*, size_t)	EEPROM read
Storage	eepromWrite	bool eepromWrite(uint16_t, const uint8_t*, size_t)	EEPROM write
System	systemReset	void systemReset()	Reset system
System	watchdogReset	void watchdogReset()	Feed watchdog
System	watchdogEnable	void watchdogEnable(uint32_t)	Enable watchdog
System	batteryVoltage	float batteryVoltage()	Battery voltage
System	boardInfo	const char* boardInfo()	Board name
System	firmwareVersion	const char* firmwareVersion()	Firmware version
Appendix B – Driver Categories
Category	Description
Motor Driver	Controls DC motors with PWM
Servo Driver	Controls servo motors
Stepper Driver	Controls stepper motors
Ultrasonic Driver	Controls HC-SR04
Line Sensor Driver	Controls TCRT5000
Touch Driver	Controls touch sensors
Light Sensor Driver	Controls photoresistor
Color Sensor Driver	Controls color sensors
LED Driver	Controls single-color LEDs
RGB LED Driver	Controls RGB LEDs
Buzzer Driver	Controls active/passive buzzers
Display Driver	Controls LCD/OLED displays
UART Driver	Controls UART
I2C Driver	Controls I2C
SPI Driver	Controls SPI
Flash Driver	Controls flash memory
EEPROM Driver	Controls EEPROM
Appendix C – Error Codes
Code	Name	Description
0	HAL_OK	Success
1	HAL_BUSY	Device busy
2	HAL_TIMEOUT	Operation timed out
3	HAL_UNSUPPORTED	Operation not supported
4	HAL_INVALID_PARAM	Invalid parameter
5	HAL_HARDWARE_FAILURE	Hardware failure
6	HAL_INIT_FAILURE	Initialization failed
Appendix D – Timing Rules
Operation	Timing	Description
delayMs	Blocking	At least ms milliseconds
delayUs	Blocking	At least us microseconds
millis	Non-blocking	Returns current uptime
micros	Non-blocking	Returns current uptime
setMotorSpeed	Immediate	Non-blocking
readUltrasonic	Non-blocking	May take ~10ms
readLineSensor	Instant	Non-blocking
readTouch	Instant	Non-blocking
readLight	Non-blocking	ADC conversion
Appendix E – Board Capability Matrix
Board	Motion	Sensor	Output	Timing	Communication	Storage	System
ESP32	✓	✓	✓	✓	✓	✓	✓
STM32	✓	✓	✓	✓	✓	✓	✓
RP2040	✓	✓	✓	✓	✓	✓	✓
Linux Sim	✓	✓	✓	✓	✓	✓	✓
Appendix F – Initialization Order
text
1. System HAL
   - boardInfo
   - systemReset (if needed)
   - watchdogEnable (optional)

2. Timing HAL
   - Start timer

3. Motion HAL
   - init motor pins
   - set initial speeds to 0

4. Output HAL
   - init LED pins
   - init buzzer pin (set OFF)

5. Sensor HAL
   - init sensor pins
   - set initial states

6. Communication HAL
   - init UART
   - init I2C
   - init SPI

7. Storage HAL
   - init flash/EEPROM