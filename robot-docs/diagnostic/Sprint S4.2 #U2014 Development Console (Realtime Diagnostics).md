# Sprint S4.2 — Development Console (Realtime Diagnostics)

**Sprint:** S4.2  
**Priority:** CRITICAL  
**Owner:** DeepSeek  
**Architecture Owner:** ChatGPT

---

# 1. Objective

Biến Diagnostic Framework hiện tại thành một công cụ quan sát realtime dành cho Development Mode.

Sprint này KHÔNG phát triển feature mới.

KHÔNG phát triển PID.

KHÔNG phát triển Line Algorithm.

Mục tiêu duy nhất:

> Cho phép developer nhìn thấy trạng thái nội bộ của robot theo thời gian thực.

Sau sprint này, mọi lỗi như:

- Sensor chập chờn
- Motor không chạy
- Timing bất thường
- Runtime quá chậm

phải được quan sát trực tiếp thay vì suy đoán.

---

# 2. Background

Sprint S4.1 đã hoàn thành:

- SensorStatistics
- Transition Counter
- Stability
- Runtime Statistics
- Diagnostic Logger

Tuy nhiên hiện tại Diagnostics chỉ lưu số liệu.

Developer vẫn không thể quan sát realtime.

Ví dụ khi che tay lên cảm biến:

Developer cần thấy ngay:

```
LEFT     HIGH

CENTER   LOW

RIGHT    LOW

MASK      100
```

thay vì phải đoán thông qua LED hoặc hành vi robot.

---

# 3. Architecture

Tạo module mới

```
core/

diagnostics/

console/
```

Ví dụ

```
DevelopmentConsole

ConsoleFormatter

ConsoleOutput
```

Không phụ thuộc RoboSim.

Không phụ thuộc Compiler.

Đây là Platform Layer.

---

# 4. Console Output

Chuẩn hóa định dạng UART.

Ví dụ

```
====================================

ROBOT DIAGNOSTICS

------------------------------------

Sensors

LEFT      HIGH

CENTER    LOW

RIGHT     LOW

MASK       100

------------------------------------

Statistics

LEFT

Reads          1234

Transitions      3

Stability     99.2%

------------------------------------

Runtime

Loop Time    1.15 ms

Loop Freq      865 Hz

Tick          10542

====================================
```

Không dùng nhiều định dạng khác nhau.

Toàn bộ project chỉ có một chuẩn.

---

# 5. Refresh Rate

Console phải hỗ trợ refresh định kỳ.

Ví dụ

```
5 Hz

10 Hz

20 Hz
```

Không spam UART.

Tần số mặc định:

```
10 Hz
```

---

# 6. Sensor Monitor

Hiển thị realtime

```
LEFT

HIGH / LOW
```

```
CENTER

HIGH / LOW
```

```
RIGHT

HIGH / LOW
```

Không chỉ thống kê.

---

# 7. Bitmask Monitor

Hiển thị

```
MASK

100

010

001

111
```

Realtime.

Đây sẽ là công cụ chính để debug Line.

---

# 8. Sensor Health

Hiển thị trạng thái.

Ví dụ

```
LEFT

Stable
```

Hoặc

```
LEFT

Noisy
```

Tiêu chí:

Có thể dựa trên

- Transition Rate
- Stability

Không cần AI.

Chỉ heuristic.

---

# 9. Runtime Panel

Hiển thị

```
Loop Time

Loop Frequency

Tick Count
```

Chuẩn bị cho profiling.

---

# 10. Logger

DiagnosticLogger không được gọi trực tiếp từ application.

DevelopmentConsole sử dụng Logger.

Kiến trúc:

```
Diagnostics

↓

ConsoleFormatter

↓

DiagnosticLogger

↓

UART
```

---

# 11. Read-only Contract

Development Console tuyệt đối:

- Không điều khiển Motor
- Không điều khiển Sensor
- Không gọi update()
- Không thay đổi Runtime

Chỉ đọc dữ liệu đã có.

---

# 12. Development Mode

Thiết kế để sau này thay UART bằng:

- BLE
- WiFi
- Desktop GUI

Không sửa DevelopmentConsole.

Chỉ thay Output Backend.

---

# 13. Physical Validation

Kiểm tra:

## Test 1

Che từng mắt.

Console phải hiển thị đúng:

```
LEFT HIGH
```

```
CENTER HIGH
```

```
RIGHT HIGH
```

---

## Test 2

Đưa robot qua line.

Quan sát

```
MASK

001

011

010

110
```

---

## Test 3

Che tay liên tục.

Nếu sensor nhiễu.

Console phải hiển thị:

```
Transitions tăng nhanh

↓

Health = NOISY
```

---

# 14. Documentation

Tạo

```
robot-docs/

S4_2_DEVELOPMENT_CONSOLE.md
```

Bao gồm

- Architecture
- Console Layout
- UART Protocol
- Refresh Strategy
- Future GUI Extension
- Sensor Health

---

# 15. Code Quality

Không hardcode chuỗi ở nhiều nơi.

Tách:

```
ConsoleFormatter
```

ra khỏi

```
ConsoleOutput
```

Chuẩn bị cho GUI.

---

# 16. Regression

Không ảnh hưởng:

- Compiler
- VM
- RobotAPI
- HAL
- Motion
- Diagnostics Statistics

Development Console chỉ đọc dữ liệu.

---

# 17. Acceptance Criteria

- [ ] DevelopmentConsole hoàn thành
- [ ] Realtime Sensor Monitor hoạt động
- [ ] Realtime Bitmask Monitor hoạt động
- [ ] Runtime Panel hoạt động
- [ ] Sensor Health hoạt động
- [ ] Refresh Rate cấu hình được
- [ ] UART Output ổn định
- [ ] Read-only Contract được đảm bảo
- [ ] Physical Validation PASS
- [ ] Documentation PASS

STOP.

Không phát triển PID.

Không phát triển Intersection.

Không phát triển GUI.

Không phát triển BLE/WiFi.

Chờ Architecture Review.