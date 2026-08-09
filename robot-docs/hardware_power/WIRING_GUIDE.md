# WIRING_GUIDE.md

**Project:** Robotics Platform

**Board:** ESP32 DevKit V1

**Hardware Version:** v1.0

---

# 1. Purpose

Tài liệu này hướng dẫn đấu dây toàn bộ robot.

Đây là tài liệu dành cho:

- Giáo viên
- Học sinh
- Người lắp ráp robot

Không mô tả Software.

Không mô tả Firmware.

Chỉ mô tả phần cứng.

---

# 2. Wiring Principle

Robot sử dụng kiến trúc sau:

```
             Battery 7.5V
                   │
      ┌────────────┴────────────┐
      │                         │
      ▼                         ▼
  TB6612FNG                 LM2596
      │                         │
      ▼                         ▼
  DC Motors                 ESP32 5V
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
                 LED            Buzzer      Sensors
```

---

# 3. ESP32 Pin Summary

| GPIO | Connected Device |
|------|------------------|
| GPIO18 | Line Sensor Left |
| GPIO16 | Line Sensor Center |
| GPIO17 | Line Sensor Right |
| GPIO19 | Active Buzzer |
| GPIO22 | HC-SR04 Echo |
| GPIO23 | HC-SR04 Trigger |
| GPIO25 | Motor Left IN1 |
| GPIO26 | Motor Left IN2 |
| GPIO27 | Motor Right IN3 |
| GPIO14 | Motor Right IN4 |
| GPIO32 | Right LED |
| GPIO33 | Left LED |

---

# 4. LED Wiring

Robot sử dụng hai LED báo trạng thái.

## Left LED

| LED | ESP32 |
|------|--------|
| + | GPIO33 |
| – | GND |

---

## Right LED

| LED | ESP32 |
|------|--------|
| + | GPIO32 |
| – | GND |

---

Lưu ý

LED phải có điện trở hạn dòng (220Ω–330Ω) nếu sử dụng LED rời.

Nếu module LED đã tích hợp điện trở thì có thể nối trực tiếp.

---

# 5. Active Buzzer Wiring

Module

```
Active Buzzer
```

| Buzzer | ESP32 |
|----------|--------|
| VCC | 3.3V |
| GND | GND |
| SIG | GPIO19 |

RobotAPI

```
SetMp3Play(id)
```

↓

GPIO19 HIGH

↓

Beep

---

# 6. Line Sensor Wiring

Module

```
3-Channel TCRT5000
```

Power

| Sensor | ESP32 |
|---------|--------|
| VCC | 3.3V |
| GND | GND |

Signal

| Sensor | GPIO |
|---------|------|
| Left | GPIO18 |
| Center | GPIO16 |
| Right | GPIO17 |

---

# 7. HC-SR04 Wiring

Power

| HC-SR04 | ESP32 |
|----------|--------|
| VCC | 5V |
| GND | GND |

Signal

| HC-SR04 | GPIO |
|----------|------|
| Trigger | GPIO23 |
| Echo | GPIO22 |

---

**Lưu ý**

Nếu module HC-SR04 xuất Echo ở mức 5V, cần sử dụng mạch chia áp hoặc level shifter để bảo vệ GPIO của ESP32 nếu cần.

---

# 8. Motor Driver Wiring

Driver

```
TB6612FNG (HW-166)
```

## Logic Control

| TB6612FNG | ESP32 |
|------------|--------|
| AIN1 | GPIO25 |
| AIN2 | GPIO26 |
| BIN1 | GPIO27 |
| BIN2 | GPIO14 |

---

## Motor Output

| TB6612FNG | Motor |
|------------|--------|
| AO1 | Left Motor |
| AO2 | Left Motor |
| BO1 | Right Motor |
| BO2 | Right Motor |

Nếu motor quay ngược chiều mong muốn:

- Đảo AO1 ↔ AO2
- Hoặc BO1 ↔ BO2

Không sửa phần mềm nếu chỉ sai chiều quay.

---

## Power

| TB6612FNG | Connection |
|------------|------------|
| VM | Battery 7.5V |
| VCC | 3.3V |
| GND | Common GND |
| STBY | 3.3V (Enable) |

---

# 9. LM2596 Wiring

Input

| LM2596 | Battery |
|---------|---------|
| IN+ | Battery + |
| IN- | Battery - |

Output

| LM2596 | ESP32 |
|---------|--------|
| OUT+ | 5V (VCC) |
| OUT- | GND |

Điều chỉnh LM2596 về **5.0V** trước khi kết nối ESP32.

---

# 10. Common Ground

Toàn bộ hệ thống phải nối chung mass.

```
Battery -

↓

LM2596 GND

↓

ESP32 GND

↓

TB6612FNG GND

↓

HC-SR04 GND

↓

Line Sensor GND

↓

LED GND

↓

Buzzer GND
```

Không được tách riêng GND.

---

# 11. Power-On Checklist

Trước khi cấp nguồn:

- [ ] LM2596 Output = 5.0V
- [ ] ESP32 chưa quá nóng
- [ ] GND đã nối chung
- [ ] Motor Driver đúng nguồn
- [ ] HC-SR04 đúng VCC/GND
- [ ] Line Sensor đúng GPIO
- [ ] LED đúng cực
- [ ] Buzzer đúng chân SIG

---

# 12. Functional Test

Sau khi nạp firmware.

Kiểm tra theo thứ tự:

## LED

```
SetLed(1)
```

↓

LED trái sáng

```
SetLed(2)
```

↓

LED phải sáng

---

## Buzzer

```
SetMp3Play(1)
```

↓

Beep

---

## Line Sensor

Che từng mắt.

↓

Development Console hiển thị đúng Bitmask.

---

## HC-SR04

Đưa vật cản.

↓

Khoảng cách thay đổi.

---

## Motor

Forward

↓

Hai bánh tiến.

Backward

↓

Hai bánh lùi.

Turn Left

↓

Robot quay trái.

Turn Right

↓

Robot quay phải.

---

# 13. Troubleshooting

## ESP32 không khởi động

- Kiểm tra LM2596 = 5V
- Kiểm tra dây VCC
- Kiểm tra GND

---

## Motor không quay

- Kiểm tra VM = 7.5V
- Kiểm tra STBY
- Kiểm tra dây motor
- Kiểm tra AIN/BIN

---

## Line Sensor không đọc

- Kiểm tra GPIO18/16/17
- Kiểm tra nguồn 3.3V
- Kiểm tra GND

---

## HC-SR04 luôn trả 0

- Kiểm tra Trigger
- Kiểm tra Echo
- Kiểm tra nguồn 5V

---

## Buzzer không kêu

- Kiểm tra GPIO19
- Kiểm tra Active Buzzer
- Kiểm tra VCC 3.3V

---

# 14. Wiring Rules

- Không cắm/rút module khi đang cấp nguồn.
- Luôn kiểm tra điện áp LM2596 trước khi cấp vào ESP32.
- Luôn sử dụng Common Ground.
- Không nối trực tiếp 7.5V vào ESP32.
- Không thay đổi GPIO nếu chưa cập nhật `HARDWARE_PINOUT.md`.

---

# 15. Document References

- HARDWARE_PINOUT.md
- POWER_ARCHITECTURE.md
- BOARD_SPEC.md
- BOM.md