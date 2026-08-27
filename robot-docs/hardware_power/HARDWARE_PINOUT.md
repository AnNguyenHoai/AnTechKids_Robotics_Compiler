# HARDWARE_PINOUT.md

**Project:** Robotics Platform

**Board:** ESP32 DevKit V1

**Hardware Version:** v1.0

**Status:** Architecture Freeze

---

# 1. Purpose

Tài liệu này định nghĩa toàn bộ GPIO Mapping của Robotics Platform.

Đây là **Single Source of Truth** cho:

- Firmware
- HAL
- RobotAPI
- Diagnostics
- RoboStudio
- Hardware Design

Mọi thay đổi GPIO phải được cập nhật tài liệu này trước khi thay đổi source code.

---

# 2. Board Information

MCU

```
ESP32 DevKit V1
```

Logic Level

```
3.3V
```

Main Supply

```
5V (từ LM2596)
```

---

# 3. GPIO Assignment

| GPIO | Module | Signal | Direction | Status |
|------:|--------|--------|-----------|--------|
| GPIO14 | Motor Driver | MOTOR_R_IN4 | Output | ✅ |
| GPIO16 | Line Sensor | CENTER | Input | ✅ |
| GPIO17 | Line Sensor | RIGHT | Input | ✅ |
| GPIO18 | Line Sensor | LEFT | Input | ✅ |
| GPIO19 | Active Buzzer | BUZZER | Output | ✅ |
| GPIO22 | HC-SR04 | ECHO | Input | ✅ |
| GPIO23 | HC-SR04 | TRIGGER | Output | ✅ |
| GPIO25 | Motor Driver | MOTOR_L_IN1 | Output | ✅ |
| GPIO26 | Motor Driver | MOTOR_L_IN2 | Output | ✅ |
| GPIO27 | Motor Driver | MOTOR_R_IN3 | Output | ✅ |
| GPIO32 | LED | RIGHT LED | Output | ✅ |
| GPIO33 | LED | LEFT LED | Output | ✅ |

---

# 4. Module Mapping

## 4.1 Line Sensor

Module

```
TCRT5000

3 Channels
```

GPIO Mapping

| Sensor | GPIO |
|---------|------|
| Left | GPIO18 |
| Center | GPIO16 |
| Right | GPIO17 |

---

### Bit Convention

```
Bit2

↓

Left
```

```
Bit1

↓

Center
```

```
Bit0

↓

Right
```

Ví dụ

| Bitmask | Meaning |
|---------|---------|
|100|Left Detect|
|010|Center Detect|
|001|Right Detect|
|110|Left + Center|
|011|Center + Right|
|111|All Detect|

Đây là Convention chính thức.

---

## 4.2 LED

Robot có 2 LED trạng thái.

| RoboSim Channel | GPIO | Position |
|-----------------|------|----------|
| 1 | GPIO33 | Left |
| 2 | GPIO32 | Right |

### Mapping Rule

```
SetLed(1)

↓

GPIO33
```

```
SetLed(2)

↓

GPIO32
```

```
SetLed(3...)

↓

Ignored
```

Các channel khác hiện chưa hỗ trợ.

---

## 4.3 Active Buzzer

GPIO

```
GPIO19
```

Logic

```
HIGH

↓

Beep
```

Implementation hiện tại:

- Digital Output
- Không PWM
- Không Melody
- Chỉ phát tiếng beep

RobotAPI

```
SetMp3Play(id)
```

---

## 4.4 Ultrasonic

Module

```
HC-SR04
```

| Signal | GPIO |
|---------|------|
| Trigger | GPIO23 |
| Echo | GPIO22 |

RobotAPI

```
GetUltrasonicDistance()
```

---

## 4.5 Motor Driver

Driver

```
TB6612FNG (HW-166)
```

### Left Motor

| Signal | GPIO |
|---------|------|
| IN1 | GPIO25 |
| IN2 | GPIO26 |

### Right Motor

| Signal | GPIO |
|---------|------|
| IN3 | GPIO27 |
| IN4 | GPIO14 |

---

### Direction Table

#### Left Motor

| IN1 | IN2 | Action |
|-----|-----|--------|
|0|0|Stop|
|1|0|Forward|
|0|1|Backward|
|1|1|Brake|

#### Right Motor

| IN3 | IN4 | Action |
|-----|-----|--------|
|0|0|Stop|
|1|0|Forward|
|0|1|Backward|
|1|1|Brake|

---

# 5. RobotAPI Mapping

| RobotAPI | Hardware |
|-----------|----------|
| SetLed() | GPIO32 / GPIO33 |
| SetMp3Play() | GPIO19 |
| Move() | TB6612FNG |
| Stop() | TB6612FNG |
| GetTraceV2I2CData() | GPIO18 / GPIO16 / GPIO17 |
| GetUltrasonicDistance() | GPIO23 / GPIO22 |

---

# 6. Diagnostics Support

Development Console hỗ trợ:

- GPIO State
- Line Sensor State
- Line Bitmask
- Sensor Stability
- Transition Counter
- Runtime Statistics

Diagnostics chỉ đọc dữ liệu.

Không điều khiển phần cứng.

---

# 7. Reserved GPIO

| GPIO | Status |
|------|--------|
| GPIO4 | Reserved |
| GPIO5 | Reserved |
| GPIO12 | Reserved |
| GPIO13 | Reserved |
| GPIO15 | Reserved |
| GPIO21 | Reserved |

Không sử dụng nếu chưa cập nhật tài liệu.

---

# 8. Hardware Summary

| Peripheral | GPIO | Status |
|------------|------|--------|
| Left Line Sensor | GPIO18 | ✅ |
| Center Line Sensor | GPIO16 | ✅ |
| Right Line Sensor | GPIO17 | ✅ |
| Left LED | GPIO33 | ✅ |
| Right LED | GPIO32 | ✅ |
| Active Buzzer | GPIO19 | ✅ |
| HC-SR04 Trigger | GPIO23 | ✅ |
| HC-SR04 Echo | GPIO22 | ✅ |
| Motor Left IN1 | GPIO25 | ✅ |
| Motor Left IN2 | GPIO26 | ✅ |
| Motor Right IN3 | GPIO27 | ✅ |
| Motor Right IN4 | GPIO14 | ✅ |

---

# 9. HAL Access Rule

Tất cả GPIO phải được truy cập theo kiến trúc sau:

```
Application
        │
        ▼
RobotAPI
        │
        ▼
HAL
        │
        ▼
GPIO
```

Không được:

```
Application

↓

GPIO
```

Không được:

```
Behavior

↓

GPIO
```

HAL là tầng duy nhất được phép truy cập trực tiếp phần cứng.

---

# 10. Future Expansion

Các module dự kiến:

- Servo
- OLED Display
- Bluetooth
- IMU
- Encoder
- RGB LED

GPIO sẽ được bổ sung trong các phiên bản sau.

---

# 11. Version History

## v1.0

- ESP32 DevKit V1
- TB6612FNG
- 3-Channel TCRT5000
- Active Buzzer
- Dual Status LED
- HC-SR04
- GPIO Architecture Freeze
## H24-B0 / H24-C Hardware V2 encoder contract

| GPIO | Function | Direction | Status |
|---|---|---|---|
| GPIO34 | ENCODER_LEFT_A | Input-only | Frozen |
| GPIO35 | ENCODER_LEFT_B | Input-only | Frozen |
| GPIO36 | ENCODER_RIGHT_A | Input-only | Frozen |
| GPIO39 | ENCODER_RIGHT_B | Input-only | Frozen |

TB6612 static wiring remains frozen as: `PWMA=3.3V`, `PWMB=3.3V`, `STBY=3.3V`. Motor direction/PWM remains on the existing four ESP32 motor control GPIOs.
