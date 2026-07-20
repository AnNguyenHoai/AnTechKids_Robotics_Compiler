#include "Sensor.h"


void Sensor::LineSensor_init()
{
#ifdef USE_LINE_SENSOR_TCRT5000
    // Gọi đúng tên hàm init() từ class driver
    Sensor_LineDetected.TRCT5000_init(); 
#endif 
}

bool Sensor::LineSensor_isLeftSensorDetected_BlackColor() {
#ifdef USE_LINE_SENSOR_TCRT5000
    // Sửa lỗi: Gọi đúng tên hàm trong class driver (Bỏ tiền tố TRCT5000_)
    return Sensor_LineDetected.TRCT5000_isLeftDetected_BlackColor();
#endif
    return false; 
}

bool Sensor::LineSensor_isCenterSensorDetected_BlackColor() {
#ifdef USE_LINE_SENSOR_TCRT5000
    return Sensor_LineDetected.TRCT5000_isCenterDetected_BlackColor();
#endif
    return false;
}

bool Sensor::LineSensor_isRightSensorDetected_BlackColor() {
#ifdef USE_LINE_SENSOR_TCRT5000
    return Sensor_LineDetected.TRCT5000_isRightDetected_BlackColor();
#endif
    return false;
}

bool Sensor::LineSensor_all_BlackColorDetected() {
#ifdef USE_LINE_SENSOR_TCRT5000
    return Sensor_LineDetected.TRCT5000_all_BlackColorDetected();
#endif
    return false;
}

bool Sensor::LineSensor_any_BlackColorDetected() {
#ifdef USE_LINE_SENSOR_TCRT5000
    return Sensor_LineDetected.TRCT5000_any_BlackColorDetected();
#endif
    return false;
}

void Sensor::LineSensor_printStatus() {
#ifdef USE_LINE_SENSOR_TCRT5000
    return Sensor_LineDetected.TRCT5000_printStatus();
#endif
}