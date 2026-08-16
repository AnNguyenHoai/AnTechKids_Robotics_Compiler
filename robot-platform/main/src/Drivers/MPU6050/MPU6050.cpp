#include "MPU6050.h"
#include <math.h>

MPU6050::MPU6050() {
    _bias.bx = 0.0f;
    _bias.by = 0.0f;
    _bias.bz = 0.0f;
}

bool MPU6050::begin(const MPU6050Config& config) {
    _config = config;

    // Khởi tạo Wire (I2C) nếu chưa được khởi tạo
    Wire.begin(MPU6050_SDA_PIN, MPU6050_SCL_PIN);

    // Kiểm tra kết nối bằng cách đọc WHO_AM_I
    uint8_t whoami = 0;
    if (!_readReg(MPU6050_WHO_AM_I, &whoami, 1) || whoami != MPU6050_WHO_AM_I_EXPECTED) {
        Serial.printf("[MPU6050] WHO_AM_I failed: got 0x%02X, expected 0x%02X\n", whoami, MPU6050_WHO_AM_I_EXPECTED);
        return false;
    }
    Serial.printf("[MPU6050] Device detected (WHO_AM_I=0x%02X)\n", whoami);

    // Wake up MPU6050 (sau reset, nó ở chế độ sleep)
    if (!_writeReg(MPU6050_PWR_MGMT_1, 0x00)) {
        Serial.println("[MPU6050] Failed to wake up device");
        return false;
    }
    delay(100);

    // Cấu hình sample rate divider
    uint8_t sampleDiv = (uint8_t)(1000 / _config.sampleRate - 1);
    if (!_writeReg(MPU6050_SMPLRT_DIV, sampleDiv)) {
        Serial.println("[MPU6050] Failed to set sample rate");
        return false;
    }

    // Cấu hình DLPF (digital low-pass filter)
    if (!_writeReg(MPU6050_CONFIG, _config.digitalFilter & 0x07)) {
        Serial.println("[MPU6050] Failed to set DLPF");
        return false;
    }

    // Cấu hình gyroscope range
    uint8_t gyroReg = 0x00;
    switch (_config.gyroRange) {
        case 250:  gyroReg = 0x00; _gyroScale = MPU6050_GYRO_SCALE_250; break;
        case 500:  gyroReg = 0x08; _gyroScale = MPU6050_GYRO_SCALE_500; break;
        case 1000: gyroReg = 0x10; _gyroScale = MPU6050_GYRO_SCALE_1000; break;
        case 2000: gyroReg = 0x18; _gyroScale = MPU6050_GYRO_SCALE_2000; break;
        default:   gyroReg = 0x00; _gyroScale = MPU6050_GYRO_SCALE_250; break;
    }
    if (!_writeReg(MPU6050_GYRO_CONFIG, gyroReg)) {
        Serial.println("[MPU6050] Failed to set gyro config");
        return false;
    }

    // Cấu hình accelerometer range
    uint8_t accelReg = 0x00;
    switch (_config.accelRange) {
        case 2:  accelReg = 0x00; _accelScale = MPU6050_ACCEL_SCALE_2G; break;
        case 4:  accelReg = 0x08; _accelScale = MPU6050_ACCEL_SCALE_4G; break;
        case 8:  accelReg = 0x10; _accelScale = MPU6050_ACCEL_SCALE_8G; break;
        case 16: accelReg = 0x18; _accelScale = MPU6050_ACCEL_SCALE_16G; break;
        default: accelReg = 0x00; _accelScale = MPU6050_ACCEL_SCALE_2G; break;
    }
    if (!_writeReg(MPU6050_ACCEL_CONFIG, accelReg)) {
        Serial.println("[MPU6050] Failed to set accel config");
        return false;
    }

    _initialized = true;
    Serial.printf("[MPU6050] Initialized: gyro=%d deg/s, accel=%d g, sample=%d Hz\n",
                  _config.gyroRange, _config.accelRange, _config.sampleRate);
    return true;
}

bool MPU6050::readAccel(MPU6050AccelData& accel) {
    if (!_initialized) return false;
    int16_t raw[3];
    if (!_readReg16(raw, MPU6050_ACCEL_XOUT_H, 3)) {
        return false;
    }
    accel.ax = raw[0] / _accelScale;
    accel.ay = raw[1] / _accelScale;
    accel.az = raw[2] / _accelScale;
    return true;
}

bool MPU6050::readGyro(MPU6050GyroData& gyro) {
    if (!_initialized) return false;
    int16_t raw[3];
    if (!_readReg16(raw, MPU6050_GYRO_XOUT_H, 3)) {
        return false;
    }
    gyro.gx = raw[0] / _gyroScale - _bias.bx;
    gyro.gy = raw[1] / _gyroScale - _bias.by;
    gyro.gz = raw[2] / _gyroScale - _bias.bz;
    return true;
}

float MPU6050::readTemperature() {
    if (!_initialized) return 0.0f;
    int16_t raw;
    if (!_readReg16(&raw, MPU6050_TEMP_OUT_H, 1)) {
        return 0.0f;
    }
    return raw / 340.0f + 36.53f;  // Công thức từ datasheet
}

int MPU6050::calibrateGyro(uint16_t samples, float stabilityThreshold) {
    if (!_initialized) {
        Serial.println("[MPU6050] Cannot calibrate: not initialized");
        return 2;  // COMMUNICATION_ERROR
    }
    Serial.printf("[MPU6050] Starting gyro calibration (%d samples)...\n", samples);
    float sumX = 0, sumY = 0, sumZ = 0;
    int valid = 0;
    float* bufX = new float[samples];
    float* bufY = new float[samples];
    float* bufZ = new float[samples];

    for (uint16_t i = 0; i < samples; i++) {
        int16_t raw[3];
        if (_readReg16(raw, MPU6050_GYRO_XOUT_H, 3)) {
            float gx = raw[0] / _gyroScale;
            float gy = raw[1] / _gyroScale;
            float gz = raw[2] / _gyroScale;
            bufX[i] = gx;
            bufY[i] = gy;
            bufZ[i] = gz;
            sumX += gx;
            sumY += gy;
            sumZ += gz;
            valid++;
        } else {
            // Lỗi đọc I2C
            delete[] bufX; delete[] bufY; delete[] bufZ;
            return 2;  // COMMUNICATION_ERROR
        }
        delay(2); // ~500 Hz sampling
    }

    if (valid == 0) {
        delete[] bufX; delete[] bufY; delete[] bufZ;
        Serial.println("[MPU6050] Calibration failed: no valid samples");
        return 2;  // COMMUNICATION_ERROR
    }

    float meanX = sumX / valid;
    float meanY = sumY / valid;
    float meanZ = sumZ / valid;

    float stdX = _computeStdDev(bufX, valid, meanX);
    float stdY = _computeStdDev(bufY, valid, meanY);
    float stdZ = _computeStdDev(bufZ, valid, meanZ);

    delete[] bufX; delete[] bufY; delete[] bufZ;

    // Kiểm tra độ ổn định
    if (stdX > stabilityThreshold || stdY > stabilityThreshold || stdZ > stabilityThreshold) {
        Serial.printf("[MPU6050] Calibration UNSTABLE: std X=%.3f Y=%.3f Z=%.3f (threshold=%.3f)\n",
                      stdX, stdY, stdZ, stabilityThreshold);
        return 1;  // UNSTABLE
    }

    _bias.bx = meanX;
    _bias.by = meanY;
    _bias.bz = meanZ;
    _calibrated = true;
    Serial.printf("[MPU6050] Calibration SUCCESS: bias X=%.3f Y=%.3f Z=%.3f deg/s\n",
                  _bias.bx, _bias.by, _bias.bz);
    return 0;  // SUCCESS
}

MPU6050Bias MPU6050::getBias() const {
    return _bias;
}

float MPU6050::_computeStdDev(const float* values, uint16_t count, float mean) {
    if (count == 0) return 0.0f;
    float sumSq = 0.0f;
    for (uint16_t i = 0; i < count; i++) {
        float diff = values[i] - mean;
        sumSq += diff * diff;
    }
    return sqrtf(sumSq / count);
}

// --- Private helpers ---

bool MPU6050::_writeReg(uint8_t reg, uint8_t value) {
    Wire.beginTransmission(_config.i2cAddress);
    Wire.write(reg);
    Wire.write(value);
    return Wire.endTransmission() == 0;
}

bool MPU6050::_readReg(uint8_t reg, uint8_t* data, size_t len) {
    Wire.beginTransmission(_config.i2cAddress);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) {
        return false;
    }
    Wire.requestFrom(_config.i2cAddress, len);
    for (size_t i = 0; i < len; i++) {
        if (Wire.available()) {
            data[i] = Wire.read();
        } else {
            return false;
        }
    }
    return true;
}

bool MPU6050::_readReg16(int16_t* dest, uint8_t reg, uint8_t count) {
    if (count == 0) return true;
    uint8_t buffer[count * 2];
    if (!_readReg(reg, buffer, count * 2)) {
        return false;
    }
    for (uint8_t i = 0; i < count; i++) {
        dest[i] = (int16_t)((buffer[i*2] << 8) | buffer[i*2+1]);
    }
    return true;
}