# RobotAPI Target Surface — Corrected Candidate

**Version:** 0.9.1

## Existing real surface

```cpp
void Forward(int16_t speed);
void Backward(int16_t speed);
void TurnLeft(int16_t speed);
void TurnRight(int16_t speed);
void Stop();
void SetMotorSpeed(int left, int right);
void Wait(uint32_t ms);

int16_t ReadUltrasonic();
int16_t ReadTouch(int port);
int16_t ReadLight(int channel);
int16_t ReadLine(int channel);
```

## Target dummy-capable surface

Names intentionally remain close to RoboSim for unresolved semantics.

```cpp
// MOTION
void SetMoveInitialize(int leftMotor, int rightMotor, /* string transport */ int reverseId);
void SetMoveRunAngle(/* string transport */ int directionId, int speed, int angle);

// SENSOR / PATROL
int32_t GetLightSensorData(int port);
int32_t GetTraceV2I2CState(int arg0, int arg1);
int32_t GetTraceV2I2C(int arg0, int arg1);

// LINE BEHAVIOR
void LineBasis(int speed);
void LineMillisecond(int speed, int millisecond);
void LineIntersectionStop(int speed, int type);
void LineTurnEncounterLine(int speed, int angle, int direction);
void LineForBmp(int speed, int degree);
void LineSetInitialize(int arg0, /* string */ int arg1Id, /* string */ int arg2Id);

// MOTOR / SERVO / STEERING
void SetMotor(int port, int speed);
void SetMotorServo(int port, int speed, int angle);
void SetMotorStraightAngle(int leftPort, int rightPort, int speed, int angle);
void SetServo(int port, int angle);
void SetSeeringEngine(int port, int angle);
void SetSeeringEngineTime(int port, int angle, int millisecond);

// LED / PERIPHERAL
void SetLightSensorLed(int port, int state);
void Set3CLed(int port, int state);
void SetLizard(int state);
```

## Important: string types are not frozen C++ ABI yet

The `int ...Id` placeholders above express the embedded transport requirement; they are **not a claim that RoboSim strings are semantically integers**.

Current embedded VM has integer-only execution storage. S3.3 must first select enum IDs or a string-table ID design. Do not declare `const char*` at RobotAPI and assume the VM can provide it.

## Query type policy

Use `int32_t` provisionally for unresolved numeric queries because VM variables are currently `int32_t`. Narrowing to `int16_t` before semantic/range evidence creates unnecessary risk.

## Dummy implementation rule

A future dummy must be observable and deterministic:

```cpp
int32_t GetTraceV2I2C(int arg0, int arg1) {
    Serial.printf("[DUMMY] GetTraceV2I2C arg0=%d arg1=%d\n", arg0, arg1);
    return 0;
}
```

The call must still traverse Adapter → Compiler → VM → RobotAPI.
