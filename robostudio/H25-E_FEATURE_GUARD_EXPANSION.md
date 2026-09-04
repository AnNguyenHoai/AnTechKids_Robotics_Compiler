# H25-E — Feature Guard Expansion

Implemented firmware feature guards for Line Sensor, Ultrasonic, Servo, and Buzzer.

- LINE_SENSOR=0: line sensors are not registered; trace APIs return neutral values; line control APIs stop safely.
- ULTRASONIC=0: ultrasonic is not registered; read API returns -1; diagnostics report disabled.
- SERVO=0: SetServo is a no-op.
- BUZZER=0: buzzer GPIO is not initialized; playback API is a no-op.

All guards use generated_device_config.h as the firmware contract.
