#ifndef IMUSENSOR_H
#define IMUSENSOR_H

#include "ISensor.h"
#include "../Drivers/MPU6050/MPU6050.h"
#include <stdint.h>

// ---- DEBUG-IMU-001: IMU Sensor Runtime Diagnostic ----
extern bool g_imuSensorRuntimeEnabled;

// ---- DEBUG-IMU-002: MPU6050 I2C Diagnostic ----
extern bool g_imuI2cEnabled;
extern bool g_imuAccelDiagnosticEnabled;
extern bool g_imuGyroDiagnosticEnabled;
extern bool g_imuTempDiagnosticEnabled;
struct IMUSample {
    uint32_t timestamp;           // milliseconds (millis())
    MPU6050AccelData accel;
    MPU6050GyroData gyro;
    float temperature;            // °C
    bool valid;
};
static void printTimingStats();
class IMUSensor : public ISensor {
public:
    IMUSensor();
    ~IMUSensor() = default;
    /**
     * Print timing statistics for I2C reads.
     * This is a diagnostic function that does not affect normal operation.
     */
    static void printTimingStats();

    /**
     * Reset timing statistics (optional, for future use).
     */
    static void resetTimingStats();
    // ISensor interface
    bool initialize() override;
    void update() override;
    bool healthy() const override;
    const char* name() const override;
    void shutdown() override;

    // Lấy mẫu mới nhất (đã được cập nhật bởi update())
    bool getLatestSample(IMUSample& sample) const;

    // Đọc trực tiếp (không cache)
    bool readAccel(MPU6050AccelData& accel);
    bool readGyro(MPU6050GyroData& gyro);
    float readTemperature();

    // Calibration: trả về 0=SUCCESS, 1=UNSTABLE, 2=COMMUNICATION_ERROR
    int calibrateGyro(uint16_t samples = 500);

    bool isCalibrated() const;
    MPU6050Bias getBias() const;
    bool isReady() const;

    // Lấy địa chỉ I2C
    uint8_t getAddress() const { return _driver.getAddress(); }

private:
    MPU6050 _driver;
    IMUSample _latestSample;
    bool _initialized;
    bool _healthy;
    const char* _name;
};

#endif // IMUSENSOR_H