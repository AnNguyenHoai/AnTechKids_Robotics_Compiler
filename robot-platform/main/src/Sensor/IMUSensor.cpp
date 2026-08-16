#include "IMUSensor.h"

IMUSensor::IMUSensor()
    : _initialized(false), _healthy(false), _name("imu") {
    _latestSample.valid = false;
    _latestSample.timestamp = 0;
}

bool IMUSensor::initialize() {
    MPU6050Config config;
    config.i2cAddress = MPU6050_DEFAULT_ADDRESS;
    config.gyroRange = 250;
    config.accelRange = 2;
    config.sampleRate = 1000;
    config.digitalFilter = 0x03;  // DLPF 42Hz

    if (!_driver.begin(config)) {
        _healthy = false;
        _initialized = false;
        return false;
    }

    _initialized = true;
    _healthy = true;
    _latestSample.valid = false;
    return true;
}

void IMUSensor::update() {
    if (!_initialized) {
        _healthy = false;
        _latestSample.valid = false;
        return;
    }

    // Đọc một mẫu đồng bộ
    IMUSample sample;
    sample.timestamp = millis();
    bool okAccel = _driver.readAccel(sample.accel);
    bool okGyro = _driver.readGyro(sample.gyro);
    sample.temperature = _driver.readTemperature();
    sample.valid = okAccel && okGyro;

    if (sample.valid) {
        _latestSample = sample;
        _healthy = true;
    } else {
        _healthy = false;
        _latestSample.valid = false;
    }
}

bool IMUSensor::healthy() const {
    return _healthy && _initialized;
}

const char* IMUSensor::name() const {
    return _name;
}

void IMUSensor::shutdown() {
    // Không cần thiết
}

bool IMUSensor::getLatestSample(IMUSample& sample) const {
    if (!_initialized || !_latestSample.valid) {
        sample.valid = false;
        return false;
    }
    sample = _latestSample;
    return true;
}

bool IMUSensor::readAccel(MPU6050AccelData& accel) {
    if (!_initialized) return false;
    return _driver.readAccel(accel);
}

bool IMUSensor::readGyro(MPU6050GyroData& gyro) {
    if (!_initialized) return false;
    return _driver.readGyro(gyro);
}

float IMUSensor::readTemperature() {
    if (!_initialized) return 0.0f;
    return _driver.readTemperature();
}

int IMUSensor::calibrateGyro(uint16_t samples) {
    if (!_initialized) return 2;  // COMMUNICATION_ERROR
    return _driver.calibrateGyro(samples, 0.5f);
}

bool IMUSensor::isCalibrated() const {
    return _driver.isCalibrated();
}

MPU6050Bias IMUSensor::getBias() const {
    return _driver.getBias();
}

bool IMUSensor::isReady() const {
    return _initialized && _healthy;
}