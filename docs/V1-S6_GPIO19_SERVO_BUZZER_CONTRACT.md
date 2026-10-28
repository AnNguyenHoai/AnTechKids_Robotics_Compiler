# V1-S6 GPIO19 exclusive Buzzer / Servo contract

## Hardware ownership
GPIO19 is an exclusive output resource on V1. In RoboStudio Hardware, disable Buzzer before enabling Servo. Selecting both is a validation error in the domain and generated-header/deployment path. Firmware additionally fails compilation if both features are on. Both off is valid.

**Physical connector caveat:** GPIO19 signal is shared, not the power rating or conditioning circuit. Before connecting SH90, verify GPIO19 reaches the connector without an inverting transistor, that GND is common and that the separate servo supply can handle start/stall current. Do not power the servo from the ESP32 3.3V pin; never hot-swap powered equipment. This commit does not verify the physical PCB.

## Implementation
- RoboSim `rcu.SetServo(port, angle)` -> frontend `set_servo` -> compiler emits opcode 36 -> VM `RobotAPI::SetServo`.
- V1 supports **one servo only**, `port=1`; `angle=0..180` with an initial conservative 1000–2000us pulse range at 50Hz. Actual mechanical safe limits must be measured before attaching gripper.
- Buzzer configuration preserves prior GPIO19 digital beep implementation.
- Servo configuration initializes GPIO19 LEDC at 50 Hz / 16-bit resolution. PWM outputs use configured ESP32 Arduino LEDC pin semantics.
- Motor/Line5 code is unchanged. Keep separate Line5 acceptance baseline.

## Safety / behavior
- GPIO19 is selected at build/flash time. Switch hardware with power OFF, update RoboStudio hardware configuration, rebuild and flash.
- Servo can retain torque after the command and while VM finishes; VM Stop does not intentionally disable servo PWM. This must be reviewed for classroom safety and gripper pinch risk.
- No overcurrent/stall sensing; no guarantee that a reboot/hang safely releases servo. Keep mechanical clearance, current-limited supply and supervised operation.
- `SetSeeringEngine` and `SetSeeringEngineTime` remain stubs.
- Capability validation should block Servo API on Buzzer-only targets; validate the complete packaging/compiler contract in CI.

## Physical acceptance (not yet run)
1. Buzzer-only build: GPIO19 beep, no servo PWM, motor Line5 baseline unchanged.
2. Servo-only build: GPIO19 measured at 50Hz; 90 degree command produces expected pulse width; 40 and 120 degree commands move without hitting stops.
3. Reject both-on hardware config and both-on firmware macro build.
4. Confirm shared connector signal is direct and servo supply/GND are correct.
5. Confirm no servo twitch during reset, boot, OTA, failed program load or motor operation.
6. Motor, ultrasonic and Line5 regressions remain passing when Servo is selected.

Do not merge as physically validated until these checks are performed.
