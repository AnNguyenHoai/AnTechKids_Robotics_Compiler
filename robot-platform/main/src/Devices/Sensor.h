#ifndef _SENSOR_H
#define _SENSOR_H

#define USE_LINE_SENSOR_TCRT5000 

#ifdef USE_LINE_SENSOR_TCRT5000
#include "../Drivers/Sensor_TRCT5000_3CH.h"
#endif

class Sensor
{
public:

#ifdef USE_LINE_SENSOR_TCRT5000
    Sensor_TRCT5000_3CH Sensor_LineDetected;
#endif    

    void LineSensor_init();
    bool LineSensor_isLeftSensorDetected_BlackColor();
    bool LineSensor_isCenterSensorDetected_BlackColor();
    bool LineSensor_isRightSensorDetected_BlackColor();    
    bool LineSensor_all_BlackColorDetected(); 
    bool LineSensor_any_BlackColorDetected();     
    void LineSensor_printStatus();
};


#endif
