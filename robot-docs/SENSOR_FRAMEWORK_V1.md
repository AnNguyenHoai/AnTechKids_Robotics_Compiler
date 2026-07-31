# Sensor Framework v1

## Architecture Overview
Application
↓
RobotAPI
↓
SensorManager (singleton)
↓
ISensor interface
├── DigitalSensor → TCRT5000, Button, Touch
├── AnalogSensor → Light, Potentiometer
├── DistanceSensor → Ultrasonic, IR Distance
├── MotionSensor → Encoder, IMU
└── Future...
↓
Hardware Abstraction (GPIO, I2C, SPI, etc.)
↓
Physical Hardware



## Layer Descriptions

- **ISensor**: Minimal lifecycle (init, update, healthy, name, shutdown).
- **SensorManager**: Singleton managing all sensors by `SensorID`.
- **DigitalSensor**: Adds `read()` method; base for digital sensors.
- **Concrete sensors**: Implement semantic APIs (e.g., `isLineDetected()`).

## Lifecycle

1. **Create** – Instantiate sensor object.
2. **Register** – Call `SensorManager::registerSensor(id, sensor)`.
3. **Initialize** – `SensorManager::initializeAll()` calls `initialize()` on every sensor.
4. **Update** – In main loop, `SensorManager::updateAll()` polls all sensors.
5. **Read** – RobotAPI queries sensor via `SensorManager::getSensor(id)` and uses semantic API.
6. **Shutdown** – (Optional) `SensorManager::shutdownAll()` releases resources.

## SensorID

Enum class `SensorID` provides compile‑time safety and fast array lookups.

```cpp
enum class SensorID : uint8_t {
    LineLeft, LineCenter, LineRight,
    Ultrasonic, Touch0, Touch1, Light, Color,
    Count
};
Adding a New Sensor
Define a new SensorID value.

Create a driver class inheriting the appropriate base (e.g., DigitalSensor).

Implement all pure virtual methods.

In RobotAPI::Initialize(), instantiate and register with SensorManager.

Add a new RobotAPI function (e.g., ReadUltrasonic()) that uses getSensor() and cast to the concrete type.

Update VM if needed (usually not, because VM calls RobotAPI).

Design Decisions
No read() in ISensor: Prevents forcing all sensors to have same reading interface.

Use of SensorID: Faster and safer than string lookup.

Semantic API: RobotAPI uses high‑level methods like isLineDetected() instead of raw values.

Dynamic allocation: Sensors are new‑ed; SensorManager owns them and deletes on shutdown.

Dependency Direction
Always one‑way:


Application → RobotAPI → SensorManager → Sensor Driver → HAL → GPIO
No reverse dependencies.



---

## 9. Cập nhật `platformio.ini` (không cần, vì thư mục Sensor đã có trong src)

---

## 10. Kiểm tra biên dịch

Sau khi thay đổi, biên dịch firmware bằng PlatformIO:

```bash
pio run -d robot-platform