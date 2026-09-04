#include "IMUSensor.h"

struct IMUTimingStats {
    uint32_t count = 0;
    uint32_t total = 0;
    uint32_t min = UINT32_MAX;
    uint32_t max = 0;
};

static IMUTimingStats g_imuTimingStats;

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

    IMUSample sample;
    sample.timestamp = millis();

    const uint32_t t0 = micros();
    const bool ok = _driver.readSample(sample.accel, sample.gyro, sample.temperature);
    const uint32_t dt = micros() - t0;

    g_imuTimingStats.count++;
    g_imuTimingStats.total += dt;
    if (dt < g_imuTimingStats.min) g_imuTimingStats.min = dt;
    if (dt > g_imuTimingStats.max) g_imuTimingStats.max = dt;

    sample.valid = ok;
    if (sample.valid) {
        _latestSample = sample;
        _healthy = true;
    } else {
        _healthy = false;
        _latestSample.valid = false;
    }
}

void IMUSensor::printTimingStats() {
    Serial.println("========================================");
    Serial.println("IMU I2C TIMING STATISTICS");
    Serial.println("----------------------------------------");

    if (g_imuTimingStats.count == 0) {
        Serial.println("No IMU reads yet");
    } else {
        const float avg = (float)g_imuTimingStats.total / g_imuTimingStats.count;
        Serial.printf("Burst sample : count=%u avg=%.2f us min=%u us max=%u us\n",
                      g_imuTimingStats.count, avg,
                      g_imuTimingStats.min, g_imuTimingStats.max);
    }
    Serial.println("========================================");
}

void IMUSensor::resetTimingStats() {
    g_imuTimingStats = IMUTimingStats();
}

bool IMUSensor::healthy() const {
    return _healthy && _initialized;
}

const char* IMUSensor::name() const {
    return _name;
}

void IMUSensor::shutdown() {
    // No explicit shutdown required for MPU6050 in the current platform.
}

bool IMUSensor::getLatestSample(IMUSample& sample) const {
    if (!_initialized || !_latestSample.valid) {
        sample.valid = false;
        return false;
    }
    sample = _latestSample;
    return true;
}

bool IMUSensor::readSample(IMUSample& sample) {
    if (!_initialized) {
        sample.valid = false;
        return false;
    }

    sample.timestamp = millis();
    sample.valid = _driver.readSample(sample.accel, sample.gyro, sample.temperature);
    return sample.valid;
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
    if (!_initialized) return 2;
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
