# S3.3B — Query Transport Foundation (TCRT5000)

## Architecture
- Sử dụng TCRT5000 HAL hiện có qua SensorManager.
- Không tạo driver mới.
- RobotAPI đọc trực tiếp từ TCRT5000 thông qua SensorManager.

## Adapter Mapping
| RoboSim | Canonical |
|---------|-----------|
| GetTraceV2I2C(port, channel) | get_trace_value(port, channel) |
| GetTraceV2I2CState(port, channel) | get_trace_state(port, channel) |
| GetTraceV2I2CData(port) | get_trace_raw(port) |
| GetTraceV2I2CChxState(port, channel) | read_line(channel) (đã có) |

## Opcode Assignments
- GetTraceValue = 42
- GetTraceState = 43
- GetTraceRaw = 44

## Implementation
- Compiler: handlers trong SensorHandler
- VM: dispatch các opcode mới
- RobotAPI: các hàm sử dụng SensorManager để đọc TCRT5000

## Test Programs
- 018_trace_query.py: test raw mask và value
- 019_trace_state_test.py: test state với LED
- 020_trace_ch_state_test.py: test ch_state với buzzer

## Regression
- PASS tất cả test hiện có.

## Inventory Update
- Tổng API: 33
- REAL: 14 (9 cũ + 2 LED + 3 trace + buzzer)
- DUMMY: 3 (SetServo, SetMotorStraightAngle, LineIntersectionStop)

## Known Limitations
- GetTraceV2I2C trả về 0 hoặc 100 (không có analog)
- GetTraceV2I2C chỉ hỗ trợ 3 kênh L/C/R (0,1,2)