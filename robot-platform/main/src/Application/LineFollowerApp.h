#ifndef LINE_FOLLOWER_APP_H
#define LINE_FOLLOWER_APP_H

#include "../Devices/Sensor.h"


class LineFollowerApp {
private:
    Sensor _sensors;          // Con trỏ liên kết sang lớp quản lý thiết bị Sensor

public:
    // Khởi tạo ứng dụng
    void LineFollowerApp_init();

    void LineFollowerApp_Main();
    
};

#endif

