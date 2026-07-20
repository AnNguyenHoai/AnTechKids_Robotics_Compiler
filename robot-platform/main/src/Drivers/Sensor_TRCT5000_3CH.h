
//When infrared sensor TRCT5000 3CH is emmitted a light source and encourted a dark color, the light is aborted, resulting in a weak reflection itensity
//Vin < Vout => HIGH(dark color)// Vin>Vout ==> LOW(light color)
#ifndef SENSOR_TRCT5000_3CH_H
#define SENSOR_TRCT5000_3CH_H

#include "../HardwareAbstraction/GPIO.h"
#include "Arduino.h"

#define LINE_DETECTED_LEVEL HIGH

class Sensor_TRCT5000_3CH
{
private:
    // Thêm const bảo vệ giá trị chân cấu hình phần cứng
    const int _pin_L = SENSOR_TRCT5000_L_PIN;
    const int _pin_C = SENSOR_TRCT5000_C_PIN;
    const int _pin_R = SENSOR_TRCT5000_R_PIN;

public:
    void TRCT5000_init();
    
    // Trả về true nếu phát hiện màu đen (Mức LOW), false nếu màu trắng (Mức HIGH)
    bool TRCT5000_isLeftDetected_BlackColor();
    bool TRCT5000_isCenterDetected_BlackColor();
    bool TRCT5000_isRightDetected_BlackColor();
    
    // Trả về true nếu BẤT KỲ kênh nào gặp màu đen
    bool TRCT5000_any_BlackColorDetected();
    
    // Trả về true nếu TẤT CẢ các kênh đều gặp màu đen
    bool TRCT5000_all_BlackColorDetected();

    // Hàm in trạng thái hệ thống ra Serial để debug
    void TRCT5000_printStatus();    
};

#endif