# MPU6050 Integration

## Hardware Connection

Kết nối MPU6050 với ESP32 qua I2C:

| MPU6050 | ESP32 |
|---------|-------|
| VCC     | 3.3V  |
| GND     | GND   |
| SCL     | GPIO22 (hoặc I2C_SCL) |
| SDA     | GPIO21 (hoặc I2C_SDA) |
| AD0     | GND (địa chỉ 0x68) hoặc 3.3V (0x69) |

## I2C Address

Mặc định: 0x68 (khi AD0 nối GND).  
Nếu AD0 nối 3.3V, địa chỉ là 0x69.

## Driver Configuration

Cấu hình mặc định:

- Gyroscope range: ±250 °/s
- Accelerometer range: ±2 g
- Sample rate: 1000 Hz
- Digital low-pass filter: DLPF_CFG = 3 (bandwidth ~42 Hz)

Có thể thay đổi trong `MPU6050Config` trước khi gọi `begin()`.

## Units

- Accelerometer: **g** (9.8 m/s²)
- Gyroscope: **degrees per second** (°/s)
- Temperature: **Celsius** (°C)

## Calibration

Gyroscope bias calibration:

1. Đặt robot đứng yên trên mặt phẳng.
2. Gửi lệnh `imu calibrate`.
3. Đợi quá trình hoàn tất (khoảng 500 mẫu, ~1 giây).
4. Bias sẽ được lưu và áp dụng cho các lần đọc sau.

**Lưu ý:** Calibration chỉ có hiệu lực cho đến khi reset. Để lưu vĩnh viễn, cần thêm lưu vào flash (chưa có trong sprint này).

## Serial Commands

| Lệnh | Mô tả |
|------|-------|
| `imu status` | Hiển thị trạng thái sensor, bias hiện tại. |
| `imu read` | Đọc và in giá trị accelerometer, gyroscope, nhiệt độ. |
| `imu calibrate` | Thực hiện calibration gyroscope (yêu cầu robot đứng yên). |

Ví dụ output:
imu status
--- IMU Status ---
Initialized: YES
Calibrated : YES
Bias X : -0.12 deg/s
Bias Y : 0.05 deg/s
Bias Z : -0.03 deg/s

imu read
Accel X=0.01 g Y=-0.02 g Z=0.99 g
Gyro X=0.03 deg/s Y=-0.01 deg/s Z=0.02 deg/s
Temp 28.15 °C

text

## Diagnostics

Nếu gặp lỗi, kiểm tra:

- Kết nối dây I2C (SCL, SDA, VCC, GND).
- Địa chỉ I2C đúng.
- Xung đột I2C với thiết bị khác.
- Sử dụng `i2cdetect` hoặc code test để kiểm tra.

## Troubleshooting

- **WHO_AM_I mismatch**: Kiểm tra nguồn và kết nối.
- **I2C communication failure**: Kiểm tra điện trở kéo lên (pull-up) trên SCL/SDA (thường 4.7kΩ).
- **Calibration fails**: Đảm bảo robot đứng yên, tránh rung lắc.
- **Dữ liệu đọc ra bất thường**: Kiểm tra cấu hình dải đo và scale.

## Known Limitations

- Chưa có lưu bias vào flash (sẽ được bổ sung trong sprint sau).
- Chưa tích hợp heading estimation (M5.6.2).
- Chưa hỗ trợ nhiều IMU cùng lúc.

## Future Extensions

- Complementary filter cho yaw estimation.
- PID controller giữ heading.
- Lưu bias vào Preferences.

Timestamp: sử dụng millis().

Calibration stability: ngưỡng std = 0.5 °/s (có thể điều chỉnh).

Kết quả calibration: SUCCESS, UNSTABLE, COMMUNICATION_ERROR.

Lưu ý về lifecycle.