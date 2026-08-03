# Sprint S4.2 — Development Console (Realtime Diagnostics)

**Sprint:** S4.2  
**Priority:** CRITICAL  
**Owner:** DeepSeek  
**Architecture Owner:** ChatGPT  

---

## 1. Overview

Development Console là một module realtime diagnostics, cho phép developer quan sát trạng thái nội bộ của robot qua UART mà không can thiệp vào runtime.

---

## 2. Architecture

Module nằm trong `robot-platform/main/src/Diagnostics/Console/` và bao gồm:

- **DevelopmentConsole** – singleton quản lý refresh rate và điều phối output.
- **ConsoleFormatter** – tạo chuỗi định dạng theo mẫu thống nhất.
- **ConsoleOutput** – backend xuất dữ liệu (hiện tại là Serial).
- **ConsoleData** – struct chứa toàn bộ dữ liệu cần hiển thị.

Luồng dữ liệu:
DiagnosticsManager + SensorManager
↓
DevelopmentConsole (định kỳ)
↓
ConsoleData
↓
ConsoleFormatter → String
↓
ConsoleOutput → UART (Serial)

text

---

## 3. Console Layout

Định dạng chuẩn:
====================================
ROBOT DIAGNOSTICS

Sensors
LEFT HIGH
CENTER LOW
RIGHT LOW
MASK 100

Statistics
LEFT
Reads 1234
Transitions 3
Stability 99.2%
CENTER
...

Health
LEFT STABLE
CENTER NOISY
RIGHT STABLE

Runtime
Loop Time 1.15 ms
Loop Freq 865 Hz
Tick 10542

Min Loop 1.10 ms
Max Loop 1.25 ms
====================================

text

---

## 4. Refresh Rate

- Mặc định: **10 Hz**.
- Có thể thay đổi qua lệnh Serial: `console rate <hz>` (1–50 Hz).
- Không spam UART quá mức.

---

## 5. Sensor Health

Heuristic:

- **STABLE** nếu `stability >= 90%` và `transitionRate <= 2%`.
- **NOISY** nếu ngược lại.

`transitionRate = transitionCount / readCount`.

---

## 6. UART Commands

| Command | Mô tả |
|---------|-------|
| `console on` | Bật console |
| `console off` | Tắt console |
| `console rate <hz>` | Đặt tần số refresh (1–50) |
| `console` | Hiển thị trạng thái console |

---

## 7. Read‑only Contract

Development Console tuyệt đối **không**:

- Điều khiển motor.
- Điều khiển sensor (không gọi `update()`).
- Thay đổi runtime.

Chỉ đọc dữ liệu đã có từ `DiagnosticsManager` và `SensorManager`.

---

## 8. Future Extensions

- Thay `ConsoleOutput` backend bằng BLE/WiFi.
- Kết nối với desktop GUI.
- Thêm các sensor khác (ultrasonic, touch, light…).

---

## 9. Regression

Không ảnh hưởng đến:

- Compiler, VM, RobotAPI, HAL, Motion, Diagnostics Statistics.

---

## 10. Acceptance Criteria

- [x] DevelopmentConsole hoàn thành
- [x] Realtime Sensor Monitor hoạt động
- [x] Realtime Bitmask Monitor hoạt động
- [x] Runtime Panel hoạt động
- [x] Sensor Health hoạt động
- [x] Refresh Rate cấu hình được
- [x] UART Output ổn định
- [x] Read-only Contract được đảm bảo
- [x] Physical Validation PASS
- [x] Documentation PASS