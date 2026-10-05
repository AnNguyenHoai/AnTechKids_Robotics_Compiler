#ifndef GPIO_H
#define GPIO_H

#include "Arduino.h"

// --- ĐỊNH NGHĨA TIỀN TỐ CHÂN CHO ROBOT (Dập tắt hoàn toàn nguy cơ trùng tên hệ thống) ---
#define ROBOT_PIN_5     5
#define ROBOT_PIN_14    14
#define ROBOT_PIN_16    16
#define ROBOT_PIN_17    17
#define ROBOT_PIN_18    18
#define ROBOT_PIN_19    19
#define ROBOT_PIN_22    22
#define ROBOT_PIN_23    23
#define ROBOT_PIN_25    25
#define ROBOT_PIN_26    26
#define ROBOT_PIN_27    27
#define ROBOT_PIN_32    32
#define ROBOT_PIN_33    33
#define ROBOT_PIN_13    13
#define ROBOT_PIN_21    21
#define ROBOT_PIN_34    34
#define ROBOT_PIN_35    35
#define ROBOT_PIN_36    36
#define ROBOT_PIN_39    39

// --- ĐẶT ALIAS (TÊN GỢI NHỚ) THEO CHỨC NĂNG PHẦN CỨNG ---

// Cảm biến vạch đường TCRT5000 5CH.
// Giữ nguyên L/C/R để tương thích V1; GPIO34/35 dành cho hai mắt ngoài.
#define SENSOR_TRCT5000_FL_PIN  ROBOT_PIN_34
#define SENSOR_TRCT5000_L_PIN   ROBOT_PIN_18
#define SENSOR_TRCT5000_C_PIN   ROBOT_PIN_16
#define SENSOR_TRCT5000_R_PIN   ROBOT_PIN_17
#define SENSOR_TRCT5000_FR_PIN  ROBOT_PIN_35

// Còi báo và Đầu ra đèn LED lớn
#define OUTPUT_BUZZER_PIN       ROBOT_PIN_19
#define OUTPUT_LED_LEFT_PIN     ROBOT_PIN_32
#define OUTPUT_LED_RIGHT_PIN    ROBOT_PIN_33

// Cảm biến siêu âm HC-SR04
#define SONIC_TRIG_PIN          ROBOT_PIN_23
#define SONIC_ECHO_PIN          ROBOT_PIN_22

// Mạch cầu H điều khiển 4 động cơ
#define MOTOR_L_IN1_PIN         ROBOT_PIN_25
#define MOTOR_L_IN2_PIN         ROBOT_PIN_26
#define MOTOR_R_IN3_PIN         ROBOT_PIN_27
#define MOTOR_R_IN4_PIN         ROBOT_PIN_14

// Cảm biến góc
#define MPU6050_SDA_PIN ROBOT_PIN_21
#define MPU6050_SCL_PIN ROBOT_PIN_13

// GPIO36/39 remain reserved input-only pins in the V1 hardware contract.
// Encoder pin ownership is intentionally not defined for the V1 Line5 baseline.

#endif
