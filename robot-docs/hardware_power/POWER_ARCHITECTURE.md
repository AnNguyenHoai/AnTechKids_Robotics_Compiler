# POWER_ARCHITECTURE.md

**Project:** Robotics Platform

**Board:** ESP32 DevKit V1

**Power Version:** v1.0

---

# 1. Purpose

Tài liệu này mô tả toàn bộ kiến trúc cấp nguồn của Robotics Platform.

Bao gồm:

- Nguồn chính
- Phân phối nguồn
- Bộ chuyển đổi điện áp
- Quy tắc nối mass (Common Ground)
- Điện áp từng module
- Quy tắc mở rộng phần cứng

Đây là tài liệu chính thức cho toàn bộ Firmware và Hardware.

---

# 2. System Power Overview

Robot sử dụng một nguồn pin duy nhất.

```
Battery Pack

7.5V
```

Nguồn 7.5V được chia thành hai nhánh:

```
Battery 7.5V
        │
        ├──────────────► Motor Driver
        │
        └──────────────► LM2596
                            │
                            ▼
                           5V
                            │
                            ▼
                          ESP32
```

---

# 3. Power Topology

```
                     +----------------------+
                     |   Battery Pack       |
                     |        7.5V          |
                     +----------+-----------+
                                |
              +-----------------+-----------------+
              |                                   |
              |                                   |
              ▼                                   ▼
      +---------------+                  +----------------+
      |   TB6612FNG   |                  |     LM2596     |
      | Motor Supply  |                  | 7.5V → 5V Buck |
      +-------+-------+                  +-------+--------+
              |                                  |
              |                                  |
              ▼                                  ▼
        DC Motors                          ESP32 DevKit
                                                |
                           +--------------------+--------------------+
                           |         |           |                  |
                           ▼         ▼           ▼                  ▼
                        LEDs     Buzzer    Line Sensor      HC-SR04
```

---

# 4. Main Power Source

Battery

```
7.5V Rechargeable Battery Pack
```

Chức năng

- Cấp nguồn cho Motor Driver
- Cấp nguồn cho LM2596

Không cấp trực tiếp vào ESP32.

---

# 5. LM2596 Buck Converter

Module

```
LM2596 DC-DC Buck Converter
```

Input

```
7.5V
```

Output

```
5.0V
```

Điện áp đầu ra phải được chỉnh trước khi kết nối.

Khuyến nghị

```
5.00V ± 0.05V
```

---

# 6. ESP32 Power

ESP32 được cấp nguồn thông qua chân:

```
VCC (5V)
```

Không sử dụng:

```
3V3
```

ESP32 sẽ tự tạo:

```
3.3V
```

để cấp cho toàn bộ GPIO.

---

# 7. Motor Power

Motor Driver

```
TB6612FNG
```

Nguồn cấp

```
Battery 7.5V
```

Motor KHÔNG đi qua LM2596.

Điều này giúp:

- Không quá tải LM2596
- Motor đủ công suất
- ESP32 ổn định hơn

---

# 8. Peripheral Power

## LED

Nguồn

```
ESP32 GPIO
```

Điện áp

```
3.3V
```

---

## Active Buzzer

Nguồn

```
ESP32
```

GPIO

```
GPIO19
```

Điện áp

```
3.3V
```

---

## Line Sensor

Module

```
TCRT5000
```

Nguồn

```
ESP32
```

Logic

```
3.3V
```

---

## HC-SR04

Nguồn

```
5V
```

Trigger

```
GPIO23
```

Echo

```
GPIO22
```

Lưu ý:

Nếu module HC-SR04 xuất Echo ở mức 5V, cần kiểm tra khả năng chịu điện áp của chân ESP32 hoặc bổ sung mạch chia áp (voltage divider) nếu cần.

---

# 9. Common Ground

Toàn bộ hệ thống phải dùng chung mass.

```
Battery (-)
        │
        ▼
 LM2596 GND
        │
        ▼
 ESP32 GND
        │
        ▼
 TB6612FNG GND
        │
        ▼
 Sensors GND
```

Không được tách riêng GND.

Nếu không dùng Common Ground:

- PWM sai
- Sensor đọc sai
- UART lỗi
- Robot hoạt động không ổn định

---

# 10. Current Distribution

```
Battery

↓

7.5V

↓

Motor Driver

↓

DC Motors
```

Song song

```
Battery

↓

LM2596

↓

5V

↓

ESP32

↓

3.3V Regulator

↓

GPIO

↓

LED

↓

Buzzer

↓

Line Sensor
```

---

# 11. Estimated Power Consumers

| Module | Voltage | Source |
|----------|---------|---------|
| ESP32 | 5V | LM2596 |
| TB6612FNG | 7.5V | Battery |
| DC Motors | 7.5V | TB6612FNG |
| Line Sensor | 3.3V | ESP32 |
| LEDs | 3.3V | ESP32 GPIO |
| Active Buzzer | 3.3V | ESP32 GPIO |
| HC-SR04 | 5V | ESP32 5V Rail |

---

# 12. Startup Sequence

Khuyến nghị khi lắp ráp:

1.

Kiểm tra LM2596

↓

Output = 5.0V

2.

Kết nối ESP32

↓

Boot thành công

3.

Kiểm tra LED

↓

PASS

4.

Kiểm tra Buzzer

↓

PASS

5.

Kiểm tra Line Sensor

↓

PASS

6.

Kiểm tra Motor

↓

PASS

---

# 13. Troubleshooting

## ESP32 Reset liên tục

Kiểm tra

- LM2596 Output
- Battery Voltage
- Common Ground

---

## Motor chạy nhưng ESP32 Reset

Kiểm tra

- Sụt áp Battery
- LM2596 quá tải
- Dây nguồn quá nhỏ

---

## Sensor đọc sai

Kiểm tra

- GND chung
- GPIO Mapping
- Điện áp 3.3V

---

## HC-SR04 không hoạt động

Kiểm tra

- Trigger GPIO23
- Echo GPIO22
- 5V cấp cho cảm biến
- GND chung

---

# 14. Future Expansion

Dự kiến bổ sung:

- Servo
- OLED Display
- Bluetooth
- Encoder
- IMU

Mọi module mới phải:

- Khai báo điện áp hoạt động
- Khai báo nguồn cấp
- Cập nhật tài liệu này

---

# 15. Architecture Rules

Application

↓

RobotAPI

↓

HAL

↓

GPIO

↓

Hardware

Application tuyệt đối không truy cập trực tiếp:

- GPIO
- Nguồn
- Peripheral

Toàn bộ phần cứng phải được quản lý thông qua HAL.

---

# 16. Version History

## v1.0

- ESP32 DevKit V1
- Battery 7.5V
- LM2596 Buck Converter
- TB6612FNG
- Active Buzzer
- Dual LED
- 3-Channel Line Sensor
- HC-SR04
- Common Ground Architecture