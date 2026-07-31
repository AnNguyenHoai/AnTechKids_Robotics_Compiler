# S3.3A.2 - Buzzer/MP3Play Implementation Report

## GPIO19 Ownership Audit
- `OUTPUT_BUZZER_PIN` = GPIO19
- Không có xung đột.

## Source Evidence
SetMp3Play được tìm thấy trong các mẫu RoboSim (bai4.py, bai5.py).

## Canonical Mapping
`rcu.SetMp3Play(index)` → `set_mp3_play(index)`

## Opcode
- Opcode: SetMp3Play = 41
- Được sinh từ api.yaml

## Changed Files
- `robot-language/specification/api.yaml`
- `robot-frontend-robosim/frontend/transformer.py`
- `robot-compiler/compiler/handlers/peripheral_handler.py` (mới)
- `robot-compiler/compiler/handlers/__init__.py`
- `robot-platform/main/src/Services/VM/VM.cpp`
- `robot-platform/main/src/Services/Robot/RobotAPI.h`
- `robot-platform/main/src/Services/Robot/RobotAPI.cpp` (sửa LED mapping)
- `examples/physical/017_buzzer_mp3play_test.py` (mới)
- `examples/physical/018_led_parity_test.py` (mới)

## LED Odd/Even Correction
- Odd port → GPIO33 (OUTPUT_LED_RIGHT_PIN)
- Even port → GPIO32 (OUTPUT_LED_LEFT_PIN)

## Index Preservation
Mọi index đều truyền nguyên vẹn đến RobotAPI.

## 200ms Adaptation
Mỗi lần gọi SetMp3Play → beep 200ms, blocking delay.

## Automated Tests
- Adapter rewrite test (literal và variable)
- Compiler test (literal và variable)
- Regression: PASS

## Board Test Procedure
1. Flash 017_buzzer_mp3play_test.py
2. Nghe thấy 3 tiếng beep (mỗi lần 200ms, cách nhau 1s)
3. Quan sát serial log có `[BUZZER] SetMp3Play index=1 -> fixed beep 200ms` etc.

## Inventory/Count Changes
- TOTAL API: 30
- Interface-supported: 15/30 = 50.0%
- REAL: 11 (Set3CLed, SetMp3Play, plus 9 cũ)
- DUMMY: 4 (SetServo, SetMotorStraightAngle, LineIntersectionStop, SetLightSensorLed)

## Limitations
- MP3 track semantics không được implement; chỉ là beep cố định.
- Blocking delay 200ms làm treo VM trong thời gian đó (chấp nhận cho sprint này).