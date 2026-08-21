#include "IMUSensor.h"

// g_imuSensorRuntimeEnabled và g_imuI2cEnabled được định nghĩa trong main.ino

IMUSensor::IMUSensor()
    : _initialized(false), _healthy(false), _name("imu") {
    _latestSample.valid = false;
    _latestSample.timestamp = 0;
}
struct IMUTimingStats {
    // Accel
    uint32_t countAccel = 0;
    uint32_t totalAccel = 0;   // microseconds
    uint32_t minAccel = UINT32_MAX;
    uint32_t maxAccel = 0;

    // Gyro
    uint32_t countGyro = 0;
    uint32_t totalGyro = 0;
    uint32_t minGyro = UINT32_MAX;
    uint32_t maxGyro = 0;

    // Temperature
    uint32_t countTemp = 0;
    uint32_t totalTemp = 0;
    uint32_t minTemp = UINT32_MAX;
    uint32_t maxTemp = 0;

    // Main loop measurement (optional)
    uint32_t loopCount = 0;
    uint32_t totalLoop = 0;
    uint32_t minLoop = UINT32_MAX;
    uint32_t maxLoop = 0;
};

static IMUTimingStats g_imuTimingStats;
static uint32_t g_lastTimingReport = 0;
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
    // ---- DEBUG-IMU-001: IMU Sensor Runtime Gate ----
    if (!g_imuSensorRuntimeEnabled) {
        _healthy = false;
        _latestSample.valid = false;
        return;
    }
    // ---- END DEBUG-IMU-001 GATE ----

    if (!_initialized) {
        _healthy = false;
        _latestSample.valid = false;
        return;
    }

    // ---- DEBUG-IMU-002: I2C Diagnostic Gate ----
    if (!g_imuI2cEnabled) {
        _healthy = false;
        _latestSample.valid = false;
        return;
    }
    // ---- END DEBUG-IMU-002 GATE ----

    // ---- NORMAL I2C READS (with sub-gates and timing) ----
    IMUSample sample;
    sample.timestamp = millis();

    bool okAccel = false;
    bool okGyro = false;
    uint32_t t0, t1;

    // ----- Accel read (with timing) -----
    if (g_imuAccelDiagnosticEnabled) {
        t0 = micros();
        okAccel = _driver.readAccel(sample.accel);
        t1 = micros();
        uint32_t dt = t1 - t0;
        g_imuTimingStats.countAccel++;
        g_imuTimingStats.totalAccel += dt;
        if (dt < g_imuTimingStats.minAccel) g_imuTimingStats.minAccel = dt;
        if (dt > g_imuTimingStats.maxAccel) g_imuTimingStats.maxAccel = dt;
    }

    // ----- Gyro read (with timing) -----
    if (g_imuGyroDiagnosticEnabled) {
        t0 = micros();
        okGyro = _driver.readGyro(sample.gyro);
        t1 = micros();
        uint32_t dt = t1 - t0;
        g_imuTimingStats.countGyro++;
        g_imuTimingStats.totalGyro += dt;
        if (dt < g_imuTimingStats.minGyro) g_imuTimingStats.minGyro = dt;
        if (dt > g_imuTimingStats.maxGyro) g_imuTimingStats.maxGyro = dt;
    }

    // ----- Temperature read (with timing) -----
    if (g_imuTempDiagnosticEnabled) {
        t0 = micros();
        sample.temperature = _driver.readTemperature();
        t1 = micros();
        uint32_t dt = t1 - t0;
        g_imuTimingStats.countTemp++;
        g_imuTimingStats.totalTemp += dt;
        if (dt < g_imuTimingStats.minTemp) g_imuTimingStats.minTemp = dt;
        if (dt > g_imuTimingStats.maxTemp) g_imuTimingStats.maxTemp = dt;
    } else {
        sample.temperature = 0.0f;
    }

    sample.valid = okAccel && okGyro;

    if (sample.valid) {
        _latestSample = sample;
        _healthy = true;
    } else {
        _healthy = false;
        _latestSample.valid = false;
    }
}
// ================================================================
// DEBUG-IMU-004: Print Timing Statistics
// ================================================================

void IMUSensor::printTimingStats() {
    Serial.println("========================================");
    Serial.println("IMU I2C TIMING STATISTICS");
    Serial.println("----------------------------------------");

    auto printStat = [](const char* name, uint32_t count, uint32_t total,
                        uint32_t minVal, uint32_t maxVal) {
        if (count == 0) {
            Serial.printf("%-10s : No reads\n", name);
            return;
        }
        float avg = (float)total / count;
        Serial.printf("%-10s : count=%5u  avg=%6.2f us  min=%5u us  max=%5u us\n",
                      name, count, avg, minVal, maxVal);
    };

    printStat("Accel", g_imuTimingStats.countAccel, g_imuTimingStats.totalAccel,
              g_imuTimingStats.minAccel, g_imuTimingStats.maxAccel);
    printStat("Gyro",  g_imuTimingStats.countGyro,  g_imuTimingStats.totalGyro,
              g_imuTimingStats.minGyro, g_imuTimingStats.maxGyro);
    printStat("Temp",  g_imuTimingStats.countTemp,  g_imuTimingStats.totalTemp,
              g_imuTimingStats.minTemp, g_imuTimingStats.maxTemp);

    Serial.println("----------------------------------------");
    Serial.printf("Total IMU updates (samples): %u\n", g_imuTimingStats.countAccel);
    Serial.println("========================================");
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
    // Lưu ý: Hàm này vẫn có thể được gọi từ bên ngoài (ví dụ lệnh imu read).
    // Nhưng trong vòng lặp chính, update() là nơi duy nhất gọi nó.
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