#include "LineFollowerApp.h"
#include "Arduino.h"


void LineFollowerApp::LineFollowerApp_init() {
    _sensors.LineSensor_init();
    Serial.println("[APP] Ứng dụng dò đường đã sẵn sàng kích hoạt.");
}


void LineFollowerApp::LineFollowerApp_Main()
{
    bool left = _sensors.LineSensor_isLeftSensorDetected_BlackColor();
    bool center = _sensors.LineSensor_isCenterSensorDetected_BlackColor();
    bool right = _sensors.LineSensor_isRightSensorDetected_BlackColor();

    if (left == true)
    {
        //Serial.println("Left Channel Detected Dark Color.");
    }
    if (center == true)
    {
        Serial.println("Center Channel Detected Dark Color.");
    }
    if (right == true)
    {
        //Serial.println("Right Channel Detected Dark Color.");
    }  
    if ((left == true)&&(center == true)&&(right == true))
    {
        //Serial.println("All Channel Detected Dark Color.");
    }
    if ((left == true)||(center == true)||(right == true))
    {
        //Serial.println("No Any Channel Detected Dark Color.");
    } 
    int value = digitalRead(16);
    Serial.println(value);

}


