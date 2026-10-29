# V1-S7: One Touch sensor on GPIO36

**Baseline:** V1 TT open-loop, after PR #431. This change affects GPIO input only. Motor, Line5, Servo/Buzzer GPIO19 and ultrasonic mappings remain unchanged.

## Pinout and wiring
- **Touch digital OUT -> ESP32 GPIO36 (VP)**.
- Touch GND -> ESP32 GND.
- Touch VCC -> module-supported supply; **OUT must never exceed 3.3V** at ESP32.
- **GPIO5 disconnected and no longer used by Touch or Light.**
- GPIO39 remains reserved for later use.
- GPIO36 is input-only, non-strapping, and has **no internal pull-up/pull-down**. A bare mechanical contact requires external pull resistor, e.g. 10 kOhm to 3.3V for active-LOW contact to ground or 10 kOhm to GND for active-HIGH contact to 3.3V. Module with actively driven 3.3V digital OUT may not need extra resistor.
- Do not use GPIO36 for output/PWM; confirm the actual PCB exposes it and that it is not allocated to other hardware.

## Software contract
- `rcu.GetTouch(1)` -> `read_touch(1)` -> `ReadTouch` VM -> `RobotAPI::ReadTouch(1)` -> `digitalRead(GPIO36)`.
- Exactly one supported logical Touch port: **1**. Other ports return `0`.
- Current driver returns **1 for HIGH** and **0 for LOW**, not necessarily 1 when pressed. Confirm sensor polarity physically before any motion exercise.
- Light Sensor GPIO5 implementation retired from V1; `ReadLight` returns neutral 0 for API compatibility. This is not a functioning Light Sensor.
- This change does not add a new RoboStudio Touch hardware toggle. Physical Touch presence still requires manual verification.

## Physical acceptance — NOT YET RUN
1. With motors lifted, wire a 3.3V-output digital Touch module to GPIO36; confirm correct GND and supply.
2. Power-cycle repeatedly with button pressed and released; ESP32 must boot without reset loops.
3. Observe GPIO36 stable transitions pressed/released; test polarity and floating behavior. Avoid moving robot until `GetTouch(1)` reads 1 when pressed.
4. Run `examples/physical/v1_s7_01_touch_gpio36_stop.py` under supervision. Robot should move when released and stop when pressed **only for active-HIGH modules**.
5. Verify existing T1/T4/T5/T6/T8 regressions remain passing; no effect on Servo/Buzzer selection.
6. Record battery state, module model, actual voltage OUT-HIGH, serial logs and repeated trial outcomes. CI is not physical evidence.

## Safety caution
This is a student-level touch input, **not an emergency-stop circuit**. VM freeze, reset, wiring faults and software polling delays can defeat it. For a real emergency stop use independent motor power cutoff. Contact bounce is not debounced in this version and should be evaluated after real-world trials.
