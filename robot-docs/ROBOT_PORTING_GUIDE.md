Robot Platform Porting Guide
Version: 1.0
Status: Architecture Freeze
Date: 2026-08-10
Owner: Robot Platform Team

Revision History
Version	Date	Author	Changes
1.0	2026-08-10	DeepSeek	Initial release
Table of Contents
Introduction

Robot Platform Architecture

Porting Philosophy

Required Components

HAL Implementation Checklist

Board Bring-up Procedure

Driver Development Rules

Capability Matrix

Validation Procedure

Certification Checklist

Common Porting Mistakes

Example Port
Appendix A: Board Checklist
Appendix B: Driver Checklist
Appendix C: HAL Checklist
Appendix D: Validation Checklist
Appendix E: Certification Checklist

Chapter 1 – Introduction
1.1 Purpose
This document explains how to port the Robot Platform to a completely new hardware platform.

It describes the required architecture and provides step-by-step guidance for implementing the Hardware Abstraction Layer (HAL) and board-specific drivers.

Porting SHALL require only:

HAL implementation

Board drivers

The following layers SHALL remain unchanged:

Runtime

Compiler

ISA

RobotAPI

1.2 Scope
This guide covers:

Required components for a new board

HAL implementation checklist

Board bring-up procedure

Driver development rules

Validation and certification process

Common porting mistakes

A complete example port

It does not cover:

Modifying the compiler or runtime

Changing the ISA specification

Hardware design or PCB layout

1.3 Supported Platforms
The Robot Platform is designed to support:

Platform	Status	Notes
ESP32 (DevKit V1)	✅ Reference	Official reference platform
STM32 (STM32F4)	🔄 Planned	Future support
RP2040 (Raspberry Pi Pico)	🔄 Planned	Future support
Linux Simulation	✅ Supported	For testing and development
Custom ARM Cortex-M	🔄 Possible	Requires HAL implementation
1.4 Target Audience
This guide is intended for:

Embedded systems engineers

Hardware engineers

Robot Platform contributors

Developers porting to new MCUs

Chapter 2 – Robot Platform Architecture
2.1 Architecture Overview
text
+------------------------------------------+
|         ROBOT PLATFORM                    |
+------------------------------------------+
|                  |                         |
|    Compiler      |       Runtime          |
|    (unchanged)   |     (unchanged)        |
+--------+---------+--------+---------------+
         |                  |
         ▼                  ▼
+------------------------------------------+
|              ROBOTAPI                     |
|             (unchanged)                   |
+------------------------------------------+
                    │
                    ▼
+------------------------------------------+
|               HAL                         |
|         (NEW for each board)              |
+------------------------------------------+
                    │
                    ▼
+------------------------------------------+
|            BOARD DRIVERS                  |
|         (NEW for each board)              |
+------------------------------------------+
                    │
                    ▼
+------------------------------------------+
|            HARDWARE                       |
|         (MCU + Peripherals)              |
+------------------------------------------+
2.2 Layers That Remain Unchanged
Layer	Reason
Compiler	Hardware-independent bytecode generation
ISA	Hardware-independent instruction set
Runtime/VM	Executes bytecode; no hardware knowledge
RobotAPI	Abstract platform API; no hardware knowledge
2.3 Layers That Must Be Replaced
Layer	Reason
HAL	Hardware abstraction must match the new MCU
Board Drivers	Specific to the new MCU peripherals
Board Support Package (BSP)	Board-specific initialization
Chapter 3 – Porting Philosophy
3.1 Core Principle
Replace HAL only. Never modify Runtime. Never modify Compiler.

The Robot Platform is designed so that porting requires zero changes to:

The compiler

The bytecode format

The virtual machine

The instruction set architecture

The RobotAPI

3.2 Runtime Reuse
The Runtime (VM) SHALL be identical on every platform.

Same source code

Same bytecode interpreter

Same instruction dispatch

Same execution model

Only the HAL implementation differs.

3.3 Compiler Reuse
The Compiler SHALL be identical on every platform.

Same source code

Same bytecode generation

Same API resolution

Same optimization passes

The compiler does not know about HAL or drivers.

3.4 HAL Only
Porting SHALL consist of:

Implementing the HAL interfaces (Chapter 5)

Implementing board drivers

Configuring the build system

Validating the port

Chapter 4 – Required Components
4.1 Board Support Package (BSP)
The BSP provides board-specific initialization.

Component	Description
Clock Configuration	CPU and peripheral clocks
Memory Configuration	SRAM, flash layout
GPIO Configuration	Pin mapping and initialization
Power Configuration	Voltage regulators, power modes
4.2 Clock
Required Interfaces:

Interface	Description
SystemClock_Config	Configure system clock
get_cpu_frequency	Get CPU frequency in MHz
get_peripheral_clock	Get peripheral bus clock
4.3 GPIO
Required Interfaces:

Interface	Description
GPIO_Init	Configure GPIO pin mode
GPIO_Write	Write to GPIO pin
GPIO_Read	Read from GPIO pin
GPIO_Toggle	Toggle GPIO pin
4.4 PWM
Required Interfaces:

Interface	Description
PWM_Init	Initialize PWM timer/channel
PWM_SetDuty	Set PWM duty cycle
PWM_Start	Start PWM output
PWM_Stop	Stop PWM output
4.5 Timer
Required Interfaces:

Interface	Description
Timer_Init	Initialize timer
Timer_Start	Start timer
Timer_Stop	Stop timer
Timer_Read	Read timer value
Timer_DelayMs	Blocking delay in milliseconds
Timer_DelayUs	Blocking delay in microseconds
4.6 UART
Required Interfaces:

Interface	Description
UART_Init	Initialize UART
UART_Send	Send data
UART_Receive	Receive data
UART_Available	Check if data available
4.7 SPI (Optional)
Interface	Description
SPI_Init	Initialize SPI
SPI_Transfer	Send/receive data
4.8 I2C (Optional)
Interface	Description
I2C_Init	Initialize I2C
I2C_Write	Write data
I2C_Read	Read data
4.9 ADC
Required Interfaces:

Interface	Description
ADC_Init	Initialize ADC
ADC_Read	Read analog value
4.10 Storage (Optional)
Interface	Description
Flash_Init	Initialize flash
Flash_Read	Read flash
Flash_Write	Write flash
Flash_Erase	Erase flash
4.11 Interrupts
Interface	Description
IRQ_Enable	Enable interrupt
IRQ_Disable	Disable interrupt
IRQ_SetPriority	Set interrupt priority
4.12 Power
Interface	Description
Power_Init	Initialize power management
Power_Sleep	Enter sleep mode
Power_Reset	Reset system
4.13 Watchdog
Interface	Description
Watchdog_Init	Initialize watchdog
Watchdog_Feed	Feed/refresh watchdog
Chapter 5 – HAL Implementation Checklist
5.1 Motion HAL Checklist
Item	Status	Description
[ ]	Required	Implement setMotorSpeed(left, right)
[ ]	Required	Implement stopMotors()
[ ]	Required	Implement brakeMotors() (can be alias to stop if not supported)
[ ]	Required	Clamp speeds to [-100, 100]
[ ]	Required	Map speed values to PWM duty cycles
[ ]	Required	Configure PWM on motor pins
[ ]	Optional	Implement getMotorSpeed(left, right)
[ ]	Required	Initialize motor pins to OFF state
5.2 Sensor HAL Checklist
Item	Status	Description
[ ]	Required	Implement readUltrasonic()
[ ]	Required	Implement readLineSensor(channel)
[ ]	Required	Implement readTouch(port)
[ ]	Required	Implement readLight(channel)
[ ]	Optional	Implement readColor()
[ ]	Required	Configure sensor GPIO pins
[ ]	Required	Handle sensor timeout/error conditions
[ ]	Required	Return normalized values
5.3 Output HAL Checklist
Item	Status	Description
[ ]	Required	Implement setLED(index, state)
[ ]	Required	Implement setBuzzer(state)
[ ]	Optional	Implement setDisplay(text)
[ ]	Required	Initialize LEDs to OFF
[ ]	Required	Initialize buzzer to OFF
5.4 Timing HAL Checklist
Item	Status	Description
[ ]	Required	Implement delayMs(ms)
[ ]	Required	Implement delayUs(us)
[ ]	Required	Implement millis()
[ ]	Required	Implement micros()
[ ]	Required	Use hardware timer for timekeeping
[ ]	Required	Ensure 32-bit overflow handling
5.5 Communication HAL Checklist
Item	Status	Description
[ ]	Required	Implement uartSend(data, length)
[ ]	Optional	Implement uartReceive(buffer, maxLength)
[ ]	Optional	Implement i2cWrite(address, data, length)
[ ]	Optional	Implement i2cRead(address, buffer, length)
[ ]	Optional	Implement spiTransfer(tx, rx, length)
5.6 Storage HAL Checklist
Item	Status	Description
[ ]	Optional	Implement flashRead(address, buffer, length)
[ ]	Optional	Implement flashWrite(address, data, length)
[ ]	Optional	Implement flashErase(address, size)
[ ]	Optional	Implement eepromRead(address, buffer, length)
[ ]	Optional	Implement eepromWrite(address, data, length)
5.7 System HAL Checklist
Item	Status	Description
[ ]	Required	Implement systemReset()
[ ]	Required	Implement boardInfo()
[ ]	Required	Implement firmwareVersion()
[ ]	Optional	Implement watchdogReset()
[ ]	Optional	Implement watchdogEnable(timeoutMs)
[ ]	Optional	Implement batteryVoltage()
Chapter 6 – Board Bring-up Procedure
6.1 Phase 1: Hardware Readiness
Step 1: Power
text
[ ] Power supply connected
[ ] Voltage levels verified
[ ] No shorts on power rails
Step 2: Clock
text
[ ] External oscillator working
[ ] Clock frequency verified
[ ] Peripheral clocks enabled
Step 3: Memory
text
[ ] SRAM accessible
[ ] Flash accessible
[ ] Memory map verified
Step 4: JTAG/SWD
text
[ ] Debug interface working
[ ] Can load and run code
[ ] Breakpoints working
6.2 Phase 2: Minimal HAL
Step 5: GPIO
text
[ ] GPIO output working
[ ] GPIO input working
[ ] LED blinks (hello world)
Step 6: UART
text
[ ] UART initialized
[ ] Can send characters
[ ] Serial output working
Step 7: Timer
text
[ ] Timer initialized
[ ] Delay working
[ ] millis() working
6.3 Phase 3: Peripheral HAL
Step 8: PWM
text
[ ] PWM initialized
[ ] Duty cycle changes observed
[ ] Frequency correct
Step 9: ADC
text
[ ] ADC initialized
[ ] ADC reads values
[ ] Values are reasonable
Step 10: Sensors
text
[ ] Ultrasonic working
[ ] Line sensor working
[ ] Touch sensor working
[ ] Light sensor working
6.4 Phase 4: RobotAPI Integration
Step 11: Motion
text
[ ] Forward command works
[ ] Backward command works
[ ] Turn command works
[ ] Stop command works
Step 12: Output
text
[ ] LED commands work
[ ] Buzzer works
[ ] Display works (if available)
6.5 Phase 5: Runtime Integration
Step 13: VM
text
[ ] Bytecode loader works
[ ] Instruction execution works
[ ] Simple program runs
Step 14: Full Program
text
[ ] Complete RoboSim program runs
[ ] All sensors work
[ ] All actuators work
[ ] No crashes
Chapter 7 – Driver Development Rules
7.1 Initialization
Every driver SHALL provide an init() function:

cpp
bool init();
Rules:

SHALL configure hardware

SHALL set initial state

SHALL return true on success, false on failure

SHALL NOT be called more than once without shutdown

7.2 Shutdown
Every driver SHALL provide a shutdown() function:

cpp
void shutdown();
Rules:

SHALL release hardware resources

SHALL set pins to safe state

SHALL be idempotent

7.3 Ownership
Rules:

Drivers own their hardware resources

No two drivers SHALL use the same GPIO pin

No two drivers SHALL use the same timer

No two drivers SHALL use the same interrupt

7.4 Error Handling
Rules:

Drivers SHALL detect hardware errors

Errors SHALL be returned as error codes

Errors SHALL NOT cause crashes

Invalid parameters SHALL be rejected

7.5 Thread Safety
Rules:

In single-threaded mode, no protection needed

In multi-threaded mode, drivers SHALL be reentrant

Shared resources SHALL be protected

7.6 Resource Management
Rules:

Resources SHALL be allocated at initialization

Resources SHALL NOT be allocated dynamically after init

Resources SHALL be released at shutdown

7.7 Driver Lifetime
text
Created (static or heap)
    │
    ▼
init() → Initialized
    │
    ▼
start() → Running
    │
    ▼
Normal Operation
    │
    ▼
shutdown() → Stopped
Chapter 8 – Capability Matrix
8.1 Mandatory Features
These features MUST be implemented for every board:

Feature	Required For
GPIO	All I/O
PWM	Motor control
Timer	Timing
UART	Serial output
ADC	Sensor reading
8.2 Optional Features
These features MAY be implemented:

Feature	Benefit
I2C	External sensors
SPI	Displays, SD cards
Flash	Persistent storage
EEPROM	Configuration storage
BLE/WiFi	Wireless communication
USB	Debugging, data transfer
Servo support	Robot arms, steering
8.3 Unsupported Features
If a feature is not supported:

Return HAL_UNSUPPORTED error

Provide a stub implementation

Document the limitation

8.4 Graceful Degradation
The platform SHALL continue to function when optional features are not present.

Example:

text
No RGB LED:
    → Set3CLed returns HAL_UNSUPPORTED
    → Program continues running

No IMU:
    → readIMU returns HAL_UNSUPPORTED
    → Program continues running

No Camera:
    → readCamera returns HAL_UNSUPPORTED
    → Program continues running
Chapter 9 – Validation Procedure
9.1 Boot Test
text
[ ] Serial output shows boot messages
[ ] All peripherals initialized
[ ] No errors reported
[ ] LED blinks (indicates boot success)
9.2 Memory Test
text
[ ] RAM size reported correctly
[ ] Flash size reported correctly
[ ] No memory corruption
[ ] Stack and heap not overlapping
9.3 Runtime Test
text
[ ] VM loads program
[ ] VM executes instructions
[ ] VM handles errors gracefully
[ ] Program completion reported
9.4 Instruction Test
text
[ ] LoadConst works
[ ] Forward/Backward works
[ ] Wait works
[ ] Compare works
[ ] Jump works
[ ] Stop works
9.5 Motion Test
text
[ ] Forward at 50% speed
[ ] Backward at 50% speed
[ ] Turn Left at 50% speed
[ ] Turn Right at 50% speed
[ ] Stop (immediate)
[ ] Different speeds: 0, 25, 50, 75, 100
9.6 Sensor Test
text
[ ] Ultrasonic reads distance
[ ] Line sensor detects line
[ ] Touch sensor detects press
[ ] Light sensor reads values
9.7 Timing Test
text
[ ] delayMs(1000) ≈ 1 second
[ ] millis() increments correctly
[ ] micros() increments correctly
9.8 RobotAPI Test
text
[ ] Forward() commands all APIs
[ ] Sensor APIs return correct values
[ ] LED commands work
[ ] Buzzer works
9.9 Stress Test
text
[ ] Continuous operation for 1 hour
[ ] No memory leaks
[ ] No crashes
[ ] No watchdog resets
9.10 Long Run Test
text
[ ] Operate for 24 hours
[ ] Periodic validation of all functions
[ ] No degradation of performance
Chapter 10 – Certification Checklist
10.1 Compiler Test
Test	Status	Description
[ ]	Required	Compiler produces bytecode
[ ]	Required	No compiler errors
[ ]	Required	No compiler warnings (or warnings are understood)
10.2 Bytecode Test
Test	Status	Description
[ ]	Required	Bytecode loads correctly
[ ]	Required	All opcodes recognized
[ ]	Required	Invalid opcode rejected
10.3 VM Test
Test	Status	Description
[ ]	Required	VM runs without errors
[ ]	Required	Error codes handled
[ ]	Required	Program counter correct
[ ]	Required	Variables correctly stored
10.4 RobotAPI Test
Test	Status	Description
[ ]	Required	All motion APIs tested
[ ]	Required	All sensor APIs tested
[ ]	Required	All output APIs tested
[ ]	Required	All timing APIs tested
10.5 HAL Test
Test	Status	Description
[ ]	Required	All required interfaces implemented
[ ]	Required	All required functions pass
[ ]	Required	Error handling works
10.6 Driver Test
Test	Status	Description
[ ]	Required	All drivers initialized
[ ]	Required	All drivers can be shutdown
[ ]	Required	No resource conflicts
10.7 Integration Test
Test	Status	Description
[ ]	Required	Compiler → VM → RobotAPI → HAL → Hardware works
[ ]	Required	Complete RoboSim program runs
[ ]	Required	All sensors and actuators work together
10.8 Hardware Test
Test	Status	Description
[ ]	Required	All hardware peripherals work
[ ]	Required	All pins assigned correctly
[ ]	Required	No electrical issues
Chapter 11 – Common Porting Mistakes
11.1 Timing Issues
Issue	Symptom	Solution
Wrong clock frequency	Timeouts, incorrect timing	Verify clock configuration
Wrong timer prescaler	delay() too slow/fast	Calculate correct prescaler
Overflow not handled	millis() wraps incorrectly	Handle 32-bit overflow
11.2 Endianness
Issue	Symptom	Solution
Big-endian target	Bytecode misread	Use little-endian by default
Mixed endianness	Data corruption	Use consistent endianness
11.3 Alignment
Issue	Symptom	Solution
Unaligned access	Hard fault	Use packed structures, disable unaligned access
11.4 Stack Size
Issue	Symptom	Solution
Stack too small	Hard fault, data corruption	Increase stack size
Stack too large	Memory waste	Profile stack usage
11.5 Memory Limits
Issue	Symptom	Solution
Insufficient RAM	VM crashes	Reduce variable count
Insufficient flash	Program won't fit	Optimize code size
11.6 GPIO Mapping
Issue	Symptom	Solution
Wrong pin numbers	Motor doesn't move	Verify pin mapping
Wrong pin mode	Sensor doesn't read	Set correct pin mode
Pin conflict	Both drivers fail	Unique pin assignment
11.7 Interrupt Conflicts
Issue	Symptom	Solution
Shared interrupt	Unexpected behavior	Clear interrupt sources
Priority inversion	Interrupts lost	Set correct priorities
Missing ISR	Hard fault	Implement all ISRs
11.8 Watchdog Reset
Issue	Symptom	Solution
Watchdog too short	Random resets	Increase timeout
Watchdog not fed	Periodic resets	Feed watchdog in main loop
11.9 Power Issues
Issue	Symptom	Solution
Brownout	Unstable operation	Check power supply
Noise	Incorrect readings	Add decoupling capacitors
Chapter 12 – Example Port
12.1 ESP32 Reference Port
This section describes the ESP32 port as a reference implementation.

Board Support Package
Component	Implementation
Clock	ESP32 SDK clock configuration
GPIO	ESP32 SDK GPIO functions
PWM	LEDC (ESP32 PWM)
Timer	ESP32 SDK timer
UART	ESP32 SDK UART
HAL Implementation
Motion HAL:

cpp
void setMotorSpeed(int left, int right) {
    left = constrain(left, -100, 100);
    right = constrain(right, -100, 100);
    // Map to PWM values
    int leftPWM = abs(left) * 255 / 100;
    int rightPWM = abs(right) * 255 / 100;
    // Set PWM outputs
    ledcWrite(PWM_CH_L_IN1, leftPWM);
    ledcWrite(PWM_CH_L_IN2, 0);
    ledcWrite(PWM_CH_R_IN3, rightPWM);
    ledcWrite(PWM_CH_R_IN4, 0);
}
Timing HAL:

cpp
void delayMs(uint32_t ms) {
    delay(ms);
}

uint32_t millis() {
    return ::millis();
}
Sensor HAL:

cpp
int16_t readUltrasonic() {
    // Trigger pulse
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    // Read echo
    uint32_t duration = pulseIn(ECHO_PIN, HIGH, 30000);
    if (duration == 0) return -1;
    return duration * 0.034 / 2;
}
Board Pin Mapping
Function	ESP32 Pin
Left Motor PWM	GPIO25/26
Right Motor PWM	GPIO27/14
Line Sensor Left	GPIO18
Line Sensor Center	GPIO16
Line Sensor Right	GPIO17
LED 1	GPIO33
LED 2	GPIO32
Buzzer	GPIO19
Ultrasonic Trigger	GPIO23
Ultrasonic Echo	GPIO22
Validation Results
Test	Status
Boot Test	✅ PASS
Memory Test	✅ PASS
Runtime Test	✅ PASS
Instruction Test	✅ PASS
Motion Test	✅ PASS
Sensor Test	✅ PASS
Timing Test	✅ PASS
RobotAPI Test	✅ PASS
Stress Test	✅ PASS
Long Run Test	✅ PASS
Appendix A – Board Checklist
Item	Status	Description
[ ]	Required	Power supply stable (5V/3.3V)
[ ]	Required	Clock source configured
[ ]	Required	Memory (RAM/Flash) accessible
[ ]	Required	Debug interface working (JTAG/SWD)
[ ]	Required	GPIO pins functional
[ ]	Required	PWM outputs functional
[ ]	Required	Timer functional
[ ]	Required	UART functional
[ ]	Required	ADC functional
[ ]	Required	Sensors connected
[ ]	Required	Motors connected
[ ]	Required	LEDs connected
[ ]	Required	Buzzer connected
Appendix B – Driver Checklist
Driver	Status	Description
Motor Driver	[ ]	PWM motor control
Servo Driver	[ ]	PWM servo control
Ultrasonic Driver	[ ]	HC-SR04 sensor
Line Sensor Driver	[ ]	TCRT5000 sensor
Touch Driver	[ ]	Touch sensor
Light Driver	[ ]	Light sensor
LED Driver	[ ]	LED control
Buzzer Driver	[ ]	Buzzer control
UART Driver	[ ]	Serial communication
I2C Driver	[ ]	I2C communication
SPI Driver	[ ]	SPI communication
Appendix C – HAL Checklist
HAL Category	Status	Description
Motion HAL	[ ]	All motion interfaces
Sensor HAL	[ ]	All sensor interfaces
Output HAL	[ ]	All output interfaces
Timing HAL	[ ]	All timing interfaces
Communication HAL	[ ]	All communication interfaces
Storage HAL	[ ]	All storage interfaces
System HAL	[ ]	All system interfaces
Appendix D – Validation Checklist
Test	Status	Description
Boot Test	[ ]	Boot messages, LED blink
Memory Test	[ ]	RAM/flash size correct
Runtime Test	[ ]	VM loads and runs
Instruction Test	[ ]	All opcodes tested
Motion Test	[ ]	All motion commands work
Sensor Test	[ ]	All sensors read correctly
Timing Test	[ ]	Timing functions accurate
RobotAPI Test	[ ]	All RobotAPI functions work
Stress Test	[ ]	1-hour continuous run
Long Run Test	[ ]	24-hour continuous run
Appendix E – Certification Checklist
Component	Status	Description
Compiler	[ ]	No errors, produces bytecode
Bytecode	[ ]	All opcodes recognized
VM	[ ]	Runs without errors
RobotAPI	[ ]	All functions tested
HAL	[ ]	All required interfaces implemented
Drivers	[ ]	All drivers initialized and working
Integration	[ ]	Full pipeline working
Hardware	[ ]	All peripherals working