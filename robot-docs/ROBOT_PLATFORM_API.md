Robot Platform API Specification
Version: 1.0
Status: Architecture Freeze
Date: 2026-08-10
Owner: Robot Platform Team

Revision History
Version	Date	Author	Changes
1.0	2026-08-10	DeepSeek	Initial release
Table of Contents
Introduction

RobotAPI Philosophy

Architecture

API Categories

Motion API

Sensor API

Output API

Timing API

System API

RobotApiRequest

RobotApiResponse

ExecutionResult Mapping

Versioning

Thread Safety

Examples
Appendix A: API Summary Table
Appendix B: Parameter Types
Appendix C: RuntimeValue Mapping
Appendix D: ExecutionResult Mapping
Appendix E: Error Table
Appendix F: Future Reserved APIs

Chapter 1 – Introduction
1.1 Purpose
This document defines the official Robot Platform API (RobotAPI) .

RobotAPI is the abstraction layer between the Runtime (Virtual Machine) and the robot hardware.

The Runtime SHALL communicate only with RobotAPI.

RobotAPI SHALL communicate with HAL (Hardware Abstraction Layer).

Hardware SHALL remain invisible to the Runtime.

RobotAPI therefore acts as the System API of the Robot Platform.

1.2 Scope
This specification covers:

All public RobotAPI functions

Input parameters and return types

Execution semantics

Error conditions and results

Request/response data structures

Version compatibility

Thread safety

It does not cover:

HAL implementation

Driver details

Hardware pinouts or registers

Compiler internals

VM execution flow (covered by ROBOT_VM_EXECUTION_MODEL.md)

1.3 Goals
The RobotAPI is designed to achieve:

Goal	Description
Hardware Independence	Same API works on any platform with a compliant HAL.
Platform Stability	API changes are backward compatible.
Deterministic Behaviour	Given identical inputs, outputs are identical.
Error Isolation	Hardware errors are contained and reported, not propagated as crashes.
Single Responsibility	RobotAPI is the only interface between Runtime and hardware.
Version Compatibility	Future versions preserve existing API semantics.
1.4 Relationship with ISA
Aspect	ISA (ROBOT_VM_ISA.md)	RobotAPI (this document)
Focus	VM instruction semantics	Platform API functions
Scope	Opcodes, operands, stack effects	C++ function signatures, parameters, results
Audience	Compiler, VM implementers	Runtime, RobotAPI implementers, HAL developers
1.5 Relationship with Runtime
The Runtime (VM) issues RobotApiRequest objects to the RobotApiDispatcher. The dispatcher routes the request to the appropriate RobotAPI function and returns a RobotApiResponse. The Runtime never calls RobotAPI functions directly; it always goes through the dispatcher.

1.6 Relationship with HAL
RobotAPI functions call HAL functions to perform hardware operations. RobotAPI does not know about GPIO registers, PWM channels, or pin numbers. HAL abstracts all hardware specifics.

Chapter 2 – RobotAPI Philosophy
2.1 Hardware Independence
RobotAPI SHALL NOT expose:

GPIO numbers

PWM channels

ADC registers

Microcontroller-specific types

Pin names

All hardware-specific details are hidden behind HAL.

2.2 Platform Independence
The same RobotAPI implementation SHALL work on:

ESP32

STM32

RP2040

Linux (simulation)

Future platforms

Only HAL changes per platform.

2.3 Stable ABI
Once a RobotAPI function is released, its signature and semantics SHALL NOT change in a way that breaks existing programs.

Deprecated functions SHALL remain available.

2.4 Deterministic Behaviour
Given the same inputs and the same hardware state, RobotAPI functions SHALL produce the same outputs and side effects.

2.5 Version Compatibility
New functions MAY be added. Existing functions SHALL NOT be removed.

2.6 Error Isolation
Hardware errors SHALL be converted to ExecutionResult status codes.

RobotAPI SHALL NOT throw exceptions.

2.7 Single Responsibility
RobotAPI is only responsible for:

Abstracting hardware

Translating runtime requests to hardware operations

Returning results and errors

RobotAPI SHALL NOT:

Implement robot algorithms

Perform scheduling

Interpret bytecode

Manage variables or stacks

Chapter 3 – Architecture
3.1 Overall Architecture
text
Virtual Machine
       │
       ▼
Instruction Handler
       │
       ▼
RobotApiDispatcher
       │
       ▼
RobotApiMapper
       │
       ▼
IRobotApi (interface)
       │
       ▼
RobotAPI Implementation
       │
       ▼
HAL (Hardware Abstraction Layer)
       │
       ▼
Drivers
       │
       ▼
Hardware
3.2 Component Responsibilities
Component	Responsibility
Virtual Machine	Executes bytecode; issues RobotApiRequest.
Instruction Handler	Translates opcode to RobotApiRequest.
RobotApiDispatcher	Validates requests, routes to mapper.
RobotApiMapper	Maps ApiId to IRobotApi method calls.
IRobotApi	Abstract interface for all robot operations.
RobotAPI	Concrete implementation; calls HAL.
HAL	Abstracts GPIO, PWM, ADC, timers, etc.
Drivers	Control individual hardware devices.
3.3 Dependency Rules
Dependencies only flow downward.

VM SHALL NOT call HAL directly.

RobotAPI SHALL NOT call VM or Runtime.

HAL SHALL NOT know about RobotAPI or VM.

Drivers SHALL NOT know about RobotAPI or VM.

3.4 Forbidden Dependencies
VM → HAL

VM → GPIO

Runtime → HAL

RobotAPI → Runtime

HAL → RobotAPI

Chapter 4 – API Categories
RobotAPI functions are grouped into logical categories.

Category	Description
Motion	Robot movement: forward, backward, turn, stop, speed control.
Sensor	Reading sensors: ultrasonic, line, touch, light, color.
Output	Actuators: LEDs, buzzer, display, servo.
Timing	Delays and timers.
System	Initialization, configuration, version info.
Future	Reserved for expansion: communication, storage, vision, navigation.
Chapter 5 – Motion API
5.1 Overview
Motion functions control the robot's drive system (motors). All speeds are specified as signed integers in the range -100 to +100, where the sign indicates direction and magnitude indicates duty cycle (percentage).

5.2 Function: Forward
Purpose: Move robot forward.

Signature:

cpp
void Forward(int16_t speed);
Parameters:

Name	Type	Range	Description
speed	int16_t	-100..100	Speed magnitude (positive forward)
Execution Result: Always success (no return value).

Failure Conditions: None.

Side Effects: Sets both motors to positive speed.

Timing: Immediate; non-blocking.

Units: Speed is percentage (0–100) of maximum PWM.

5.3 Function: Backward
Purpose: Move robot backward.

Signature:

cpp
void Backward(int16_t speed);
Parameters:

Name	Type	Range	Description
speed	int16_t	-100..100	Speed magnitude (positive backward)
Execution Result: Always success.

Side Effects: Sets both motors to negative speed.

5.4 Function: TurnLeft
Purpose: Turn robot left (rotate in place).

Signature:

cpp
void TurnLeft(int16_t speed);
Parameters:

Name	Type	Range	Description
speed	int16_t	-100..100	Speed magnitude
Execution Result: Always success.

Side Effects: Left motor negative, right motor positive.

5.5 Function: TurnRight
Purpose: Turn robot right (rotate in place).

Signature:

cpp
void TurnRight(int16_t speed);
Parameters:

Name	Type	Range	Description
speed	int16_t	-100..100	Speed magnitude
Execution Result: Always success.

Side Effects: Left motor positive, right motor negative.

5.6 Function: Stop
Purpose: Immediately stop all motors.

Signature:

cpp
void Stop();
Parameters: None.

Execution Result: Always success.

Side Effects: Sets both motors to 0.

Timing: Immediate.

5.7 Function: SetMotorSpeed
Purpose: Set left and right motor speeds independently.

Signature:

cpp
void SetMotorSpeed(int left, int right);
Parameters:

Name	Type	Range	Description
left	int	-100..100	Left motor speed
right	int	-100..100	Right motor speed
Execution Result: Always success.

Side Effects: Sets both motors to specified speeds.

Timing: Immediate.

5.8 Function: SetMoveInitialize
Purpose: Configure drive motor ports and reverse mode (stub in current implementation).

Signature:

cpp
void SetMoveInitialize(int leftMotor, int rightMotor, const char* reverse);
Parameters:

Name	Type	Description
leftMotor	int	Port number for left motor
rightMotor	int	Port number for right motor
reverse	string	Reverse mode ("left_reversal", "right_reversal", etc.)
Execution Result: Always success (stub).

Future: Will configure motor direction.

5.9 Function: SetMoveRunAngle
Purpose: Move in a direction for a specified wheel angle (approximated by time).

Signature:

cpp
void SetMoveRunAngle(const char* direction, int speed, int angle);
Parameters:

Name	Type	Description
direction	string	"forward", "backward", "left", "right"
speed	int	Speed (-100..100)
angle	int	Angle in degrees (wheel rotation)
Execution Result: May return error if angle exceeds limits.

Side Effects: Blocks until movement completes (approximated).

Timing: Blocking; uses timing approximation.

Chapter 6 – Sensor API
6.1 Overview
Sensor functions read data from various sensors. All sensor reads are non-blocking and return immediately.

6.2 Function: ReadUltrasonic
Purpose: Read distance from ultrasonic sensor (HC-SR04).

Signature:

cpp
int16_t ReadUltrasonic();
Parameters: None.

Return Type: int16_t (distance in cm).

Return Range: 0..400 (cm) or -1 on error/timeout.

Failure Conditions: Returns -1 if sensor is unhealthy or times out.

Timing: Non-blocking; polls hardware.

Units: Centimeters.

6.3 Function: ReadTouch
Purpose: Read touch sensor state.

Signature:

cpp
int16_t ReadTouch(int port);
Parameters:

Name	Type	Range	Description
port	int	0..N-1	Touch sensor port number
Return Type: int16_t (0 = not pressed, 1 = pressed).

Return Range: 0 or 1.

Failure Conditions: Returns 0 if port is invalid.

Timing: Instant.

6.4 Function: ReadLight
Purpose: Read light sensor value (analog).

Signature:

cpp
int16_t ReadLight(int channel);
Parameters:

Name	Type	Range	Description
channel	int	0..N-1	Sensor channel
Return Type: int16_t (raw ADC value).

Return Range: 0..4095 (depends on ADC resolution).

Failure Conditions: Returns 0 if invalid.

Timing: Non-blocking.

6.5 Function: ReadColor
Purpose: Read color sensor (placeholder).

Signature:

cpp
int16_t ReadColor();
Parameters: None.

Return Type: int16_t (dummy).

Return Range: 0.

Failure Conditions: None.

Future: Will return color ID.

6.6 Function: ReadLine
Purpose: Read digital line sensor (TCRT5000).

Signature:

cpp
int16_t ReadLine(int channel);
Parameters:

Name	Type	Range	Description
channel	int	0..2	0=Left, 1=Center, 2=Right
Return Type: int16_t (0 = no line, 1 = line detected).

Return Range: 0 or 1.

Failure Conditions: Returns 0 if invalid.

Timing: Non-blocking.

6.7 Function: GetTraceValue
Purpose: Get trace sensor value (0/50/100 based on line detection).

Signature:

cpp
int16_t GetTraceValue(int port, int channel);
Parameters:

Name	Type	Description
port	int	Port number (ignored)
channel	int	Channel 0..2 (Left, Center, Right)
Return Type: int16_t (100 if line detected, 0 otherwise).

Return Range: 0 or 100.

Failure Conditions: Returns 0 if invalid.

Timing: Non-blocking.

6.8 Function: GetTraceState
Purpose: Get boolean trace sensor state.

Signature:

cpp
bool GetTraceState(int port, int channel);
Parameters:

Name	Type	Description
port	int	Port number (ignored)
channel	int	Channel 0..2
Return Type: bool (true if line detected).

Return Range: true/false.

Failure Conditions: Returns false if invalid.

6.9 Function: GetTraceRaw
Purpose: Get raw bitmask of all 3 trace sensors.

Signature:

cpp
int16_t GetTraceRaw(int port);
Parameters:

Name	Type	Description
port	int	Port number (ignored)
Return Type: int16_t (3-bit mask: bit2=Left, bit1=Center, bit0=Right).

Return Range: 0..7.

Failure Conditions: Returns 0 if sensors unavailable.

6.10 Function: GetLightSensorData
Purpose: Read light sensor digital state (dummy).

Signature:

cpp
int16_t GetLightSensorData(int port);
Parameters:

Name	Type	Description
port	int	Port number
Return Type: int16_t (always 0 in current implementation).

Return Range: 0.

Failure Conditions: None.

Semantic: Dummy (returns deterministic value).

Chapter 7 – Output API
7.1 Overview
Output functions control actuators: LEDs, buzzer, servo.

7.2 Function: Set3CLed
Purpose: Set 3-color LED (on/off).

Signature:

cpp
void Set3CLed(int port, int state);
Parameters:

Name	Type	Description
port	int	Port number (1..N)
state	int	0 = OFF, 1 = ON
Execution Result: Always success.

Side Effects: Turns LED on/off.

Hardware Mapping: Odd ports → GPIO33, even ports → GPIO32.

7.3 Function: SetLightSensorLed
Purpose: Set light sensor LED (on/off).

Signature:

cpp
void SetLightSensorLed(int port, int state);
Parameters:

Name	Type	Description
port	int	Port number
state	int	0 = OFF, 1 = ON
Execution Result: Always success.

Side Effects: Turns sensor LED on/off.

7.4 Function: SetMp3Play
Purpose: Play MP3 track (adapted to active buzzer beep).

Signature:

cpp
void SetMp3Play(int index);
Parameters:

Name	Type	Description
index	int	Track index (ignored)
Execution Result: Always success.

Side Effects: Produces a 200ms beep on the active buzzer.

Timing: Blocking (200ms delay).

Note: This is an approximation; no MP3 decoding is performed.

7.5 Function: SetServo
Purpose: Set servo angle (stub).

Signature:

cpp
void SetServo(int port, int angle);
Parameters:

Name	Type	Description
port	int	Servo port
angle	int	Angle in degrees (0..180)
Execution Result: Always success (stub).

Side Effects: None (dummy).

Future: Will control actual servo.

7.6 Function: SetSeeringEngine
Purpose: Set steering engine angle (stub).

Signature:

cpp
void SetSeeringEngine(int port, int angle);
Parameters:

Name	Type	Description
port	int	Port
angle	int	Angle in degrees
Execution Result: Always success.

7.7 Function: SetSeeringEngineTime
Purpose: Set steering engine angle and hold for time (stub).

Signature:

cpp
void SetSeeringEngineTime(int port, int angle, int millisecond);
Parameters:

Name	Type	Description
port	int	Port
angle	int	Angle
millisecond	int	Hold time in ms
Execution Result: Always success.

7.8 Function: SetMotor
Purpose: Set DC motor speed (stub).

Signature:

cpp
void SetMotor(int port, int speed);
Parameters:

Name	Type	Description
port	int	Motor port
speed	int	Speed (-100..100)
Execution Result: Always success.

7.9 Function: SetMotorServo
Purpose: Set motor+servo combination (stub).

Signature:

cpp
void SetMotorServo(int port, int speed, int angle);
Parameters:

Name	Type	Description
port	int	Port
speed	int	Speed
angle	int	Angle
Execution Result: Always success.

7.10 Function: SetMotorStraightAngle
Purpose: Move both motors for a given angle (stub).

Signature:

cpp
void SetMotorStraightAngle(int leftPort, int rightPort, int speed, int angle);
Parameters:

Name	Type	Description
leftPort	int	Left motor port
rightPort	int	Right motor port
speed	int	Speed
angle	int	Angle in degrees
Execution Result: Always success.

7.11 Function: SetLizard
Purpose: Control peripheral lizard (stub).

Signature:

cpp
void SetLizard(int state);
Parameters:

Name	Type	Description
state	int	State
Execution Result: Always success.

Chapter 8 – Timing API
8.1 Function: Wait
Purpose: Blocking delay in milliseconds.

Signature:

cpp
void Wait(uint32_t ms);
Parameters:

Name	Type	Range	Description
ms	uint32_t	0..2^32-1	Delay in milliseconds
Execution Result: Always success.

Side Effects: Blocks the calling thread (in current single-threaded model, blocks the VM).

Timing: Blocking for ms milliseconds.

Units: Milliseconds.

Chapter 9 – System API
9.1 Function: Initialize
Purpose: Initialize all hardware (motors, sensors, LEDs, buzzer).

Signature:

cpp
void Initialize();
Parameters: None.

Execution Result: Always success.

Side Effects: Configures GPIO, PWM, sensors, sets initial state.

Timing: Non-blocking.

Chapter 10 – RobotApiRequest
10.1 Purpose
RobotApiRequest encapsulates a request from the VM to the RobotAPI.

10.2 Structure
cpp
class RobotApiRequest {
public:
    RobotApiRequest();
    RobotApiRequest(ApiId apiId, const std::vector<RuntimeValue>& params);

    ApiId apiId() const;
    const std::vector<RuntimeValue>& parameters() const;
    void setApiId(ApiId id);
    void setParameters(const std::vector<RuntimeValue>& params);
    void addParameter(const RuntimeValue& value);

    void setExecutionContextId(uint64_t id);
    uint64_t executionContextId() const;

    void setTimestamp(std::chrono::steady_clock::time_point ts);
    std::chrono::steady_clock::time_point timestamp() const;

private:
    ApiId m_apiId;
    std::vector<RuntimeValue> m_parameters;
    uint64_t m_contextId;
    std::chrono::steady_clock::time_point m_timestamp;
};
10.3 Fields
Field	Type	Description
apiId	ApiId	Identifies the API function to call.
parameters	std::vector<RuntimeValue>	Parameters for the API call.
contextId	uint64_t	Execution context ID (reserved).
timestamp	std::chrono::steady_clock::time_point	Timestamp when request was created.
10.4 ApiId Enum
cpp
enum class ApiId : uint32_t {
    UNKNOWN = 0,
    FORWARD = 1,
    BACKWARD = 2,
    TURN_LEFT = 3,
    TURN_RIGHT = 4,
    STOP = 5,
    WAIT = 6,
    SET_LED = 7,
    READ_ULTRASONIC = 8,
    READ_TOUCH = 9,
    READ_LIGHT = 10,
    READ_LINE = 11,
    PLAY_BUZZER = 12,
    READ_COLOR = 13,
    // Future...
};
10.5 Ownership Rules
The VM creates the request.

The dispatcher copies the request (or moves it).

The RobotAPI processes it synchronously.

The request is destroyed after the response is generated.

Chapter 11 – RobotApiResponse
11.1 Purpose
RobotApiResponse encapsulates the result of a RobotAPI call.

11.2 Structure
cpp
class RobotApiResponse {
public:
    RobotApiResponse();
    explicit RobotApiResponse(bool success);

    bool success() const;
    void setSuccess(bool success);

    void setReturnValue(const RuntimeValue& value);
    std::optional<RuntimeValue> returnValue() const;

    void setDiagnostic(const std::string& msg);
    std::string diagnostic() const;

    void setExecutionTime(std::chrono::microseconds us);
    std::chrono::microseconds executionTime() const;

private:
    bool m_success;
    std::optional<RuntimeValue> m_returnValue;
    std::string m_diagnostic;
    std::chrono::microseconds m_executionTime;
};
11.3 Fields
Field	Type	Description
success	bool	True if the call succeeded.
returnValue	std::optional<RuntimeValue>	Return value (if any).
diagnostic	std::string	Human-readable diagnostic message.
executionTime	std::chrono::microseconds	Execution time of the call.
Chapter 12 – ExecutionResult Mapping
12.1 Purpose
ExecutionResult is the unified result type used by the VM and Runtime to represent the outcome of instruction execution.

12.2 Mapping from RobotApiResult
RobotAPI returns RobotApiResult (a platform-independent status). The dispatcher converts it to ExecutionResult.

12.3 Status Mapping
RobotApiResult Status	ExecutionResult Status	Error Code
OK	Success	0
ERROR	Failure	1
UNSUPPORTED	Failure	2
TIMEOUT	Failure	3
BUSY	Failure	4
UNKNOWN	Failure	5
12.4 ExecutionResult Structure
cpp
struct ExecutionResult {
    ExecutionStatus status;          // Success, Failure, Error, Pending
    uint32_t errorCode;              // Numeric error code
    std::string diagnosticMessage;   // Human-readable message
    uint32_t programCounter;         // PC after execution
    ExecutionLayer layer;            // Which layer produced the result
    uint32_t opcodeId;               // Opcode being executed
    std::chrono::microseconds executionTime;
};
Chapter 13 – Versioning
13.1 API Version
The RobotAPI version SHALL be independent of the VM and ISA versions.

13.2 Version Number
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (rare)

MINOR: New functions added

PATCH: Bug fixes, no API changes

13.3 Backward Compatibility
Existing functions SHALL NOT change signature.

Existing functions SHALL NOT change semantics.

New functions MAY be added.

13.4 Forward Compatibility
New functions SHALL use new ApiId values.

Unused ApiId values are reserved.

The dispatcher SHALL reject unknown ApiId.

13.5 Deprecation
Deprecated functions SHALL remain available.

Deprecation SHALL be documented.

A deprecation warning MAY be emitted.

Chapter 14 – Thread Safety
14.1 Current Model
The RobotAPI is single-threaded.

The VM executes one instruction at a time.

Only one thread calls RobotAPI.

14.2 Future Multi-threaded Model
Future versions MAY support multiple threads.

RobotAPI functions SHALL be reentrant.

Global state SHALL be protected.

14.3 Concurrency Restrictions
No two threads SHALL call the same function concurrently.

All functions are non-reentrant unless specified.

14.4 Ownership
RobotAPI owns hardware state.

Hardware state is global.

No ownership transfer to VM.

Chapter 15 – Examples
15.1 Motion Example
Request
cpp
RobotApiRequest request(ApiId::FORWARD, {RuntimeValue(80)});
Response
cpp
RobotApiResponse response(true);
response.setDiagnostic("Forward 80");
response.setExecutionTime(chrono::microseconds(10));
15.2 Sensor Example
Request
cpp
RobotApiRequest request(ApiId::READ_ULTRASONIC, {});
Response
cpp
RobotApiResponse response(true);
response.setReturnValue(RuntimeValue(25)); // 25 cm
response.setDiagnostic("Ultrasonic read");
15.3 Error Example
Request
cpp
RobotApiRequest request(ApiId::READ_LINE, {RuntimeValue(5)});
Response (invalid channel)
cpp
RobotApiResponse response(false);
response.setDiagnostic("Invalid channel");
Appendix A – API Summary Table
Category	Function	Signature	Description
Motion	Forward	void Forward(int16_t speed)	Move forward
Motion	Backward	void Backward(int16_t speed)	Move backward
Motion	TurnLeft	void TurnLeft(int16_t speed)	Turn left
Motion	TurnRight	void TurnRight(int16_t speed)	Turn right
Motion	Stop	void Stop()	Stop motors
Motion	SetMotorSpeed	void SetMotorSpeed(int left, int right)	Set speeds
Motion	SetMoveInitialize	void SetMoveInitialize(int, int, const char*)	Configure (stub)
Motion	SetMoveRunAngle	void SetMoveRunAngle(const char*, int, int)	Move angle (approx)
Sensor	ReadUltrasonic	int16_t ReadUltrasonic()	Distance in cm
Sensor	ReadTouch	int16_t ReadTouch(int port)	Touch state
Sensor	ReadLight	int16_t ReadLight(int channel)	Light value
Sensor	ReadColor	int16_t ReadColor()	Color (dummy)
Sensor	ReadLine	int16_t ReadLine(int channel)	Line detect
Sensor	GetTraceValue	int16_t GetTraceValue(int, int)	Trace value
Sensor	GetTraceState	bool GetTraceState(int, int)	Trace state
Sensor	GetTraceRaw	int16_t GetTraceRaw(int)	Raw mask
Sensor	GetLightSensorData	int16_t GetLightSensorData(int)	Light data (dummy)
Output	Set3CLed	void Set3CLed(int, int)	LED on/off
Output	SetLightSensorLed	void SetLightSensorLed(int, int)	Sensor LED
Output	SetMp3Play	void SetMp3Play(int)	Play beep
Output	SetServo	void SetServo(int, int)	Servo angle (stub)
Output	SetSeeringEngine	void SetSeeringEngine(int, int)	Steering (stub)
Output	SetSeeringEngineTime	void SetSeeringEngineTime(int, int, int)	Steering time (stub)
Output	SetMotor	void SetMotor(int, int)	Motor speed (stub)
Output	SetMotorServo	void SetMotorServo(int, int, int)	Motor servo (stub)
Output	SetMotorStraightAngle	void SetMotorStraightAngle(int, int, int, int)	Motor angle (stub)
Output	SetLizard	void SetLizard(int)	Lizard (stub)
Timing	Wait	void Wait(uint32_t ms)	Delay
System	Initialize	void Initialize()	Hardware init
Appendix B – Parameter Types
Type	C++ Type	Description
int16_t	int16_t	16-bit signed integer
int	int	32-bit signed integer
uint32_t	uint32_t	32-bit unsigned integer
bool	bool	Boolean
string	const char*	Null-terminated string
Appendix C – RuntimeValue Mapping
RobotAPI Type	RuntimeValue Type	Description
int16_t	IntegerValue	16-bit signed integer
int	IntegerValue	32-bit signed integer
uint32_t	IntegerValue	32-bit unsigned integer
bool	BooleanValue	Boolean
string	StringValue	String
void	(none)	No value
Appendix D – ExecutionResult Mapping
ExecutionResult Status	Description
Success	API call completed successfully.
Failure	API call failed (recoverable).
Error	Fatal error (unrecoverable).
Appendix E – Error Table
Error Code	Name	Description
0	OK	Success
1	UNKNOWN_API	Unknown ApiId
2	INVALID_PARAM	Invalid parameter value
3	TIMEOUT	Operation timed out
4	BUSY	Hardware busy
5	UNSUPPORTED	Operation not supported
6	HARDWARE_ERROR	Hardware failure
Appendix F – Future Reserved APIs
Category	Reserved APIs
Motion	Rotate, Curve, FollowPath
Sensor	ReadIMU, ReadEncoder, ReadGyroscope, ReadCamera
Output	OLED, LCD, Matrix
Communication	UART, I2C, SPI, BLE, WiFi
Storage	EEPROM, SDCard
Vision	Camera, ImageProcessing
Navigation	GPS, Odometry