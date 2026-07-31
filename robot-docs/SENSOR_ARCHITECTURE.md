# Sensor Architecture

## Overview

The sensor subsystem is designed with clear layer separation to ensure hardware independence and extensibility.
Application
↓
RobotAPI
↓
Sensor Framework (SensorManager + ISensor)
↓
Sensor Driver (TCRT5000, Ultrasonic, etc.)
↓
GPIO / I2C / SPI

text

## Design Principles

1. **Layer Separation** – RobotAPI never touches GPIO directly; only drivers access hardware.
2. **Driver Independence** – Each driver is self‑contained and knows nothing about RobotAPI or VM.
3. **Semantic API** – Drivers expose high‑level methods like `isLineDetected()`, not raw `digitalRead()`.
4. **Hardware Replaceable** – Switching from TCRT5000 to another sensor requires only a new driver class; RobotAPI remains unchanged.

## Components

- **ISensor** – abstract interface with lifecycle methods.
- **SensorManager** – singleton that registers, initializes, updates, and provides diagnostics for all sensors.
- **Concrete Drivers** – e.g., `TCRT5000`, `Ultrasonic`, `Touch`, etc., all implement ISensor.

## Lifecycle

1. **Registration** – RobotAPI creates sensor instances and registers them with SensorManager.
2. **Initialization** – SensorManager calls `initialize()` on all sensors.
3. **Update** – In the main loop, `SensorManager::updateAll()` is called to refresh readings.
4. **Read** – RobotAPI queries SensorManager for a sensor by name and calls `read()`.