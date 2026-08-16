# Heading Hold Controller

## Overview

Heading Hold Controller sử dụng MPU6050 và Relative Heading Estimator để giữ robot đi thẳng theo hướng đã định, bù trừ sai lệch do động cơ không đồng đều, pin yếu, hoặc mặt đường không phẳng.

## Control Model
Base Speed (user command)
↓
Static Motor Calibration (leftMotorScale, rightMotorScale, speedScale)
↓
Calibrated Base L/R
↓
Dynamic Heading Correction (from PID)
↓
Direction Transform (Forward/Backward)
↓
Clamp (-100..100)
↓
PWM Output

text

## Numerical Example

Với cấu hình hiện tại:
- `leftMotorScale = 0.820`
- `rightMotorScale = 1.000`
- `speedScale = 1.000`

### Forward, base = 50

**Không correction:**
- L = 50 × 0.820 = 41
- R = 50 × 1.000 = 50

**Correction = +5 (quay trái):**
- L = 41 - 5 = 36
- R = 50 + 5 = 55
- Kết quả: L < R → quay trái

**Correction = -5 (quay phải):**
- L = 41 - (-5) = 46
- R = 50 + (-5) = 45
- Kết quả: L > R → quay phải

### Backward, base = 50

**Correction = +5 (quay trái khi lùi):**
- L = -(41) - 5 = -46
- R = -(50) + 5 = -45
- Kết quả: L < R (âm hơn) → quay trái

**Correction = -5 (quay phải khi lùi):**
- L = -(41) - (-5) = -36
- R = -(50) + (-5) = -55
- Kết quả: L > R → quay phải

## Direction Convention

- **Gyro Z > 0**: heading tăng → robot quay trái.
- **Gyro Z < 0**: heading giảm → robot quay phải.
- **HeadingController error**: `error = target - current`.
- **Positive error**: yêu cầu quay trái.
- **Negative error**: yêu cầu quay phải.

## Timing Architecture

HeadingController tự quản lý timing:
- `update(currentHeading, timestamp)` được gọi với timestamp từ `millis()`.
- Lần gọi đầu tiên sau reset/start: chỉ lưu timestamp, không tính dt.
- Lần gọi sau: tính dt = timestamp - lastTimestamp, giới hạn ≤ 0.1s.
- `reset()`: xóa timing state và PID state.

## PID Lifecycle

- **Start motion**: capture current heading → reset PID/timing → HOLDING.
- **Stop motion**: disable controller → reset PID/timing.
- **Calibration SUCCESS**: reset HeadingEstimator → reset HeadingController.

## Calibration Gating

Heading Hold chỉ hoạt động khi IMU đã được hiệu chỉnh (`imu isCalibrated`). Nếu IMU mất calib hoặc mất kết nối trong lúc đang chạy, Heading Hold tự động tắt, robot tiếp tục chạy với tốc độ base.

## Diagnostics

Lệnh `heading control` hiển thị:
--- Heading Control ---
State : HOLDING
IMU Calibrated: YES
Target : +12.40 deg
Current : +10.70 deg
Error : +1.70 deg
Correction : +4.20
Kp : 1.20
Ki : 0.00
Kd : 0.10
MaxCorrection : 20
Effective L : 36
Effective R : 55

text

## PID Tuning (Initial Values)

- Kp = 1.2
- Ki = 0
- Kd = 0.1
- MaxCorrection = 20

Đây là giá trị khởi tạo. Việc tuning sẽ được thực hiện sau physical test.

## Physical Validation

**Trạng thái: PENDING**

Chưa thực hiện test trên robot thật. Sẽ được thực hiện sau khi code được review và phê duyệt.

## Test Procedure (dự kiến)

1. `imu calibrate` → đảm bảo IMU calibrated.
2. `heading status` → xác nhận heading ≈ 0°.
3. Tắt heading hold (nếu cần).
4. Chạy Forward ở tốc độ thấp (20–30), ghi nhận độ lệch tự nhiên.
5. Bật heading hold.
6. Chạy Forward cùng tốc độ, ghi nhận độ lệch.
7. So sánh kết quả.
8. Trong lúc chạy, tạo nhiễu nhẹ → kiểm tra controller phản hồi đúng hướng.