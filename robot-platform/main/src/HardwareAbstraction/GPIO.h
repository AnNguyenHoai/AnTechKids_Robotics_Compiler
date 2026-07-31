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

// --- ĐẶT ALIAS (TÊN GỢI NHỚ) THEO CHỨC NĂNG PHẦN CỨNG ---

// Cảm biến vạch đường TCRT5000 3CH
#define SENSOR_TRCT5000_L_PIN   ROBOT_PIN_18  
#define SENSOR_TRCT5000_C_PIN   ROBOT_PIN_16   // Lưu ý: Nếu dùng GPIO5, hãy đổi dòng trên thành ROBOT_PIN_5 5
#define SENSOR_TRCT5000_R_PIN   ROBOT_PIN_17  

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

#endif