# S4.1 — Robot Diagnostics Framework

## Architecture

Diagnostics Framework là một module độc lập, nằm trong `robot-platform/main/src/Diagnostics/`.  
Nó cung cấp khả năng thu thập thống kê và xuất báo cáo về trạng thái của robot mà không can thiệp vào logic điều khiển chính.

### Components

- **DiagnosticsManager** – Singleton quản lý toàn bộ diagnostics.
- **SensorStatistics** – Cấu trúc dữ liệu thống kê cho mỗi sensor.
- **RollingBuffer** – Bộ đệm vòng 100 mẫu để tính stability.
- **DiagnosticLogger** – Công cụ in báo cáo ra UART (Serial).

### Sensor Diagnostics

Hiện tại hỗ trợ TCRT5000 (line sensors). Mỗi sensor cung cấp:

- `readCount` – tổng số lần đọc.
- `highCount` / `lowCount` – số lần HIGH/LOW.
- `transitionCount` – số lần chuyển trạng thái (0→1 hoặc 1→0).
- `stability` – phần trăm HIGH trong 100 lần đọc gần nhất.

### Runtime Diagnostics

- `tickCount` – số vòng lặp chính.
- `loopFrequency` – tần số vòng lặp (Hz).
- `lastLoopTime`, `minLoopTime`, `maxLoopTime` – thời gian thực hiện mỗi vòng lặp (µs).

## Usage

Trong Serial Monitor, gõ lệnh:
diagnostics

text

hoặc
diag

text

Sẽ in ra báo cáo có dạng:
==============================
Sensor Diagnostics
--- LEFT ---
Reads 10540
HIGH 5200
LOW 5340
Transitions 182
Stability 97.8%
--- CENTER ---
...
--- RIGHT ---
...
--- Runtime ---
Ticks 10540
Loop freq 87.2 Hz
Last loop 11456 us
Min loop 11023 us
Max loop 12890 us
==============================

text

## Design Decisions

- **Read‑only** – Không thay đổi hành vi robot.
- **Tách biệt** – Không phụ thuộc vào RoboSim, Compiler hay VM.
- **Mở rộng** – Dễ dàng thêm diagnostics cho motor, IMU, v.v.
- **Nhẹ** – Sử dụng ít tài nguyên, không làm chậm vòng lặp chính.

## Future Extensions

- Motor Diagnostics (PWM, encoder, tốc độ thực)
- GUI Integration qua UART (json)
- WiFi / BLE streaming
- Lưu log vào flash
