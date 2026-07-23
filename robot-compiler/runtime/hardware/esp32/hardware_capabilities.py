# runtime/hardware/esp32/hardware_capabilities.py
class HardwareCapabilities:
    def __init__(self):
        self.supports_pwm = True
        self.supports_adc = True
        self.supports_gpio = True
        self.supports_uart = True
        self.supports_i2c = True
        self.supports_spi = True
        self.max_pwm_channels = 16
        self.max_adc_channels = 8
        self.max_gpio_pins = 40
        self.has_encoder = False
        self.has_gyroscope = False