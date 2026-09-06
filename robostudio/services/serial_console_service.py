"""RoboStudio serial console service for direct USB robot communication."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

DEFAULT_BAUD_RATE = 115200


class SerialConsoleError(RuntimeError):
    """Raised when the serial console cannot be used."""


class SerialConsoleService(QObject):
    """Own the USB serial connection and expose non-blocking Qt signals."""

    data_received = Signal(str)
    connection_changed = Signal(bool, str)
    error_occurred = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        try:
            from PySide6.QtSerialPort import QSerialPort
        except ImportError as exc:
            raise SerialConsoleError(
                "Qt Serial Port support is unavailable. Reinstall PySide6 with QtSerialPort support."
            ) from exc
        self._serial_port_class = QSerialPort
        self._port = QSerialPort(self)
        self._port.setBaudRate(DEFAULT_BAUD_RATE)
        self._port.readyRead.connect(self._read_available)
        self._port.errorOccurred.connect(self._on_error)

    @staticmethod
    def available_ports() -> list[tuple[str, str]]:
        """Return (port_name, description) pairs for currently visible ports."""
        try:
            from PySide6.QtSerialPort import QSerialPortInfo
        except ImportError:
            return []
        ports = []
        for info in QSerialPortInfo.availablePorts():
            description = info.description() or info.manufacturer() or "Serial device"
            ports.append((info.portName(), description))
        return sorted(ports, key=lambda item: item[0].lower())

    @property
    def is_connected(self) -> bool:
        return self._port.isOpen()

    @property
    def port_name(self) -> str:
        return self._port.portName()

    def connect_port(self, port_name: str, baud_rate: int = DEFAULT_BAUD_RATE) -> bool:
        """Open a selected serial port without blocking the UI."""
        port_name = port_name.strip()
        if not port_name:
            self.error_occurred.emit("Select a USB serial port first.")
            return False
        if self._port.isOpen():
            if self._port.portName() == port_name and self._port.baudRate() == baud_rate:
                return True
            self.disconnect_port()
        self._port.setPortName(port_name)
        self._port.setBaudRate(baud_rate)
        if not self._port.open(self._serial_port_class.ReadWrite):
            message = self._port.errorString() or "Unable to open serial port."
            self.error_occurred.emit(f"Serial connection failed: {message}")
            return False
        self._port.clear(self._serial_port_class.AllDirections)
        self.connection_changed.emit(True, f"Connected to {port_name} @ {baud_rate}")
        return True

    def disconnect_port(self) -> None:
        """Close the serial port and discard buffered data."""
        if self._port.isOpen():
            name = self._port.portName()
            self._port.close()
            self.connection_changed.emit(False, f"Disconnected from {name}")

    def send(self, command: str, append_newline: bool = True) -> bool:
        """Send one console command; newline is appended by default."""
        if not self._port.isOpen():
            self.error_occurred.emit("Serial port is not connected.")
            return False
        text = command if not append_newline else command.rstrip("\r\n") + "\n"
        written = self._port.write(text.encode("utf-8"))
        if written == -1:
            self.error_occurred.emit(
                f"Serial write failed: {self._port.errorString() or 'unknown error'}"
            )
            return False
        return True

    def _read_available(self) -> None:
        data = bytes(self._port.readAll())
        if data:
            self.data_received.emit(data.decode("utf-8", errors="replace"))

    def _on_error(self, error) -> None:
        if error == self._serial_port_class.NoError:
            return
        if error in (self._serial_port_class.ResourceError, self._serial_port_class.DeviceNotFoundError):
            message = self._port.errorString() or "Serial device disconnected."
            if self._port.isOpen():
                self._port.close()
            self.connection_changed.emit(False, f"Serial disconnected: {message}")
            self.error_occurred.emit(message)

    def close(self) -> None:
        self.disconnect_port()
