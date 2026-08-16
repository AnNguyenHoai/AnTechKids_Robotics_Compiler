#ifndef MPU6050_H
#define MPU6050_H

#include <Arduino.h>
#include <Wire.h>
#include "../../HardwareAbstraction/GPIO.h"
// Cấu hình mặc định
#define MPU6050_DEFAULT_ADDRESS     0x68
#define MPU6050_WHO_AM_I            0x75
#define MPU6050_WHO_AM_I_EXPECTED   0x68

// Các thanh ghi chính
#define MPU6050_PWR_MGMT_1          0x6B
#define MPU6050_SMPLRT_DIV          0x19
#define MPU6050_CONFIG              0x1A
#define MPU6050_GYRO_CONFIG         0x1B
#define MPU6050_ACCEL_CONFIG        0x1C
#define MPU6050_ACCEL_XOUT_H        0x3B
#define MPU6050_GYRO_XOUT_H         0x43
#define MPU6050_TEMP_OUT_H          0x41

// Các hằng số chia tỉ lệ (tương ứng với các dải đo)
#define MPU6050_ACCEL_SCALE_2G      16384.0f   // LSB/g
#define MPU6050_ACCEL_SCALE_4G      8192.0f
#define MPU6050_ACCEL_SCALE_8G      4096.0f
#define MPU6050_ACCEL_SCALE_16G     2048.0f

#define MPU6050_GYRO_SCALE_250      131.0f     // LSB/(°/s)
#define MPU6050_GYRO_SCALE_500      65.5f
#define MPU6050_GYRO_SCALE_1000     32.8f
#define MPU6050_GYRO_SCALE_2000     16.4f

struct MPU6050Config {
    uint8_t i2cAddress = MPU6050_DEFAULT_ADDRESS;
    uint16_t gyroRange = 250;        // 250, 500, 1000, 2000
    uint16_t accelRange = 2;         // 2, 4, 8, 16
    uint16_t sampleRate = 1000;      // Hz
    uint8_t digitalFilter = 0x03;    // DLPF_CFG (0-6)
};

struct MPU6050AccelData {
    float ax;    // g
    float ay;
    float az;
};

struct MPU6050GyroData {
    float gx;    // deg/s
    float gy;
    float gz;
};

struct MPU6050Bias {
    float bx;
    float by;
    float bz;
};

class MPU6050 {
public:
    MPU6050();
    ~MPU6050() = default;

    // Khởi tạo, trả về true nếu thành công
    bool begin(const MPU6050Config& config = MPU6050Config());

    // Đọc dữ liệu
    bool readAccel(MPU6050AccelData& accel);
    bool readGyro(MPU6050GyroData& gyro);
    float readTemperature();  // °C

    // Calibration: thu thập N mẫu khi robot đứng yên
    // Trả về: 0 = SUCCESS, 1 = UNSTABLE, 2 = COMMUNICATION_ERROR
    int calibrateGyro(uint16_t samples = 500, float stabilityThreshold = 0.5f);

    // Lấy bias hiện tại
    MPU6050Bias getBias() const;

    // Địa chỉ I2C
    uint8_t getAddress() const { return _config.i2cAddress; }

    // Trạng thái
    bool isReady() const { return _initialized; }
    bool isCalibrated() const { return _calibrated; }

private:
    bool _writeReg(uint8_t reg, uint8_t value);
    bool _readReg(uint8_t reg, uint8_t* data, size_t len);
    bool _readReg16(int16_t* dest, uint8_t reg, uint8_t count);  // count = số lượng int16_t
    float _computeStdDev(const float* values, uint16_t count, float mean);

    MPU6050Config _config;
    MPU6050Bias   _bias;
    bool _initialized = false;
    bool _calibrated = false;

    float _accelScale;   // LSB/g
    float _gyroScale;    // LSB/(°/s)
};

#endif // MPU6050_H