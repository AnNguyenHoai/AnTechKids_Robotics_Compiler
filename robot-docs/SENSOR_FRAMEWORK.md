# Sensor Framework

## SensorManager

The SensorManager is a singleton that:

- Maintains a list of `ISensor*`.
- Provides `registerSensor()`, `initializeAll()`, `updateAll()`, `diagnostics()`.
- Allows lookup by name via `getSensor()`.

## ISensor Interface

All sensors must implement:

| Method | Description |
|--------|-------------|
| `initialize()` | Configures hardware (GPIO, etc.). Returns `true` on success. |
| `update()` | Polls hardware and stores latest value. Called periodically. |
| `healthy()` | Returns `true` if sensor is operational. |
| `name()` | Returns a unique string identifier. |
| `read()` | Returns the latest raw integer value. |

## Adding a New Sensor

1. Create a class that inherits from `ISensor`.
2. Implement all pure virtual methods.
3. In `RobotAPI::Initialize()`, instantiate the sensor and call `SensorManager::instance().registerSensor(...)`.
4. Expose a high‑level API in RobotAPI (e.g., `ReadUltrasonic()`) that uses `getSensor()` and `read()`.
5. Update VM binding if needed (usually not, because VM calls RobotAPI).