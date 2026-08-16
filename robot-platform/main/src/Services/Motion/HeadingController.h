#ifndef HEADING_CONTROLLER_H
#define HEADING_CONTROLLER_H

#include "../Line/PIDController.h"
#include <stdint.h>

class HeadingController {
public:
    HeadingController();

    // Khởi tạo với PID gains và max correction
    void init(float kp, float ki, float kd, float maxCorrection);

    // Bắt đầu giữ heading: capture target từ current heading
    void start(float currentHeading);

    // Cập nhật controller với heading hiện tại và timestamp (millis)
    // Trả về correction (có thể âm hoặc dương)
    float update(float currentHeading, uint32_t timestamp);

    // Dừng heading hold, reset PID và timing
    void stop();

    // Reset PID state và timing state
    void reset();

    // Trạng thái
    bool isActive() const { return _active; }
    float getTargetHeading() const { return _targetHeading; }

    // PID gains (cho diagnostics)
    float getKp() const { return _kp; }
    float getKi() const { return _ki; }
    float getKd() const { return _kd; }
    float getMaxCorrection() const { return _maxCorrection; }

    // Lấy heading error và correction cuối cùng
    float getLastError() const { return _lastError; }
    float getLastCorrection() const { return _lastCorrection; }

private:
    // Chuẩn hóa góc về [-180, 180]
    float normalizeAngle(float angle);

    PIDController _pid;
    float _kp, _ki, _kd;
    float _maxCorrection;
    float _targetHeading;
    bool _active;
    float _lastError;
    float _lastCorrection;
    bool _pidInitialized;

    // Timing state (owned by controller)
    bool _firstUpdate;
    uint32_t _lastTimestamp;
};

#endif // HEADING_CONTROLLER_H