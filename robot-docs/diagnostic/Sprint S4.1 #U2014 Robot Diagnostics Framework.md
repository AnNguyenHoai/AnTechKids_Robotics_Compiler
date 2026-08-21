# Sprint S4.1 — Robot Diagnostics Framework

**Sprint:** S4.1  
**Priority:** CRITICAL  
**Owner:** DeepSeek  
**Architecture Owner:** ChatGPT

---

# 1. Objective

Xây dựng Diagnostic Framework cho toàn bộ Robot Platform.

Đây KHÔNG phải feature.

Đây là hạ tầng phục vụ:

- Hardware Validation
- Sensor Debug
- Motor Debug
- Performance Analysis
- Future Development Mode GUI

Sau sprint này, mọi hardware mới đều phải có khả năng tự chẩn đoán.

---

# 2. Design Philosophy

Hiện tại việc debug phải dựa vào:

- LED
- Robot chạy hay không
- Quan sát bằng mắt

Điều này không đủ.

Mục tiêu của sprint:

Thay vì đoán:

```
Robot không rẽ trái

↓

Không biết lỗi ở đâu
```

Phải đạt:

```
Diagnostics

↓

Left Sensor

↓

Transition = 187/s

↓

Stability = 52%

↓

=> Sensor không ổn định
```

---

# 3. Architecture

Tạo module mới

```
core/

diagnostics/
```

Ví dụ

```
DiagnosticsManager

SensorDiagnostics

MotorDiagnostics

RuntimeDiagnostics
```

KHÔNG phụ thuộc RoboSim.

Đây là Platform Layer.

---

# 4. Sensor Diagnostics

Áp dụng đầu tiên cho:

```
TCRT5000
```

Theo interface

```
SensorDiagnostics
```

---

## Statistics

Mỗi sensor cần thống kê:

```cpp
struct SensorStatistics
{
    uint32_t readCount;

    uint32_t highCount;

    uint32_t lowCount;

    uint32_t transitionCount;

    uint32_t lastTransitionTime;

    float stability;
};
```

---

## API

Ví dụ

```cpp
SensorStatistics GetStatistics();
```

---

# 5. Stability

Định nghĩa

```
100 lần đọc

↓

HIGH = 98

LOW = 2

↓

Stable = 98%
```

Document rõ công thức.

---

# 6. Transition Counter

Theo dõi:

```
0

↓

1

↓

0

↓

1
```

Mỗi lần đổi trạng thái.

Ví dụ

```
transition = 124
```

Transition quá cao:

=> Sensor nhiễu.

---

# 7. Realtime Bitmask

Cho phép đọc realtime

```
Mask

001

010

100

111
```

Không dùng print().

Xuất qua Diagnostic Layer.

---

# 8. Runtime Diagnostics

Theo dõi:

```
Loop Frequency

Loop Time

Tick Count

Sensor Read Frequency
```

Ví dụ

```
Loop

1.18 ms
```

---

# 9. Motor Diagnostics

Chuẩn bị interface.

Chưa implement.

Ví dụ

```
MotorStatistics
```

Để sprint sau.

---

# 10. UART Debug Channel

Không dùng

```
Serial.print()
```

trực tiếp.

Tạo

```
DiagnosticLogger
```

Ví dụ

```cpp
DiagnosticLogger::Print(...)

DiagnosticLogger::PrintStatistics(...)
```

Sau này có thể redirect sang:

- UART
- BLE
- WiFi
- GUI

Không sửa code.

---

# 11. Development Mode

Thiết kế theo hướng:

```
ESP32

↓

Diagnostic Layer

↓

UART

↓

PC GUI
```

Không cần GUI trong sprint này.

Chỉ chuẩn bị kiến trúc.

---

# 12. Example

Ví dụ UART:

```
==============================

Sensor Diagnostics

LEFT

Reads          10540

HIGH           5200

LOW            5340

Transitions    182

Stability      97.8%

------------------------------

CENTER

...

------------------------------

RIGHT

...

Mask

100

Loop

1.23 ms

==============================
```

---

# 13. Physical Validation

Thực hiện:

- Che tay từng mắt
- Đưa lên line
- Thay đổi ánh sáng

Quan sát:

- Transition
- Stability
- Mask

Mục tiêu:

Xác định được nguyên nhân nếu sensor không ổn định.

---

# 14. Regression

Không ảnh hưởng:

- Compiler
- VM
- RobotAPI
- HAL
- Motion
- Line
- LED

Diagnostic phải là read-only.

Không thay đổi hành vi robot.

---

# 15. Documentation

Tạo

```
robot-docs/

S4_1_DIAGNOSTICS_FRAMEWORK.md
```

Bao gồm

- Architecture
- Statistics
- Runtime
- UART
- Future GUI
- Extension Guide

---

# 16. Acceptance Criteria

- [ ] DiagnosticsManager hoàn thành
- [ ] SensorStatistics hoạt động
- [ ] Transition Counter hoạt động
- [ ] Stability hoạt động
- [ ] Runtime Diagnostics hoạt động
- [ ] DiagnosticLogger hoạt động
- [ ] UART report hoạt động
- [ ] Không ảnh hưởng Robot Runtime
- [ ] Physical Validation PASS
- [ ] Documentation PASS

STOP.

Không làm PID.

Không làm Motor PID.

Không làm GUI.

Không làm BLE.

Không làm WiFi.

Chờ Architecture Review.