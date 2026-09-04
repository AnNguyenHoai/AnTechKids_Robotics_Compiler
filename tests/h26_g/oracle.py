"""H26-G runtime-neutral execution oracle."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class TraceEvent:
    kind: str
    args: tuple[object, ...] = ()

    def as_tuple(self) -> tuple[object, ...]:
        return (self.kind, *self.args)


def event(kind: str, *args: object) -> TraceEvent:
    return TraceEvent(kind, tuple(args))


def normalize_hardware_log(log: Iterable[Sequence[object]]) -> tuple[TraceEvent, ...]:
    """Map runtime/hardware telemetry to semantic oracle events."""
    result: list[TraceEvent] = []
    for item in log:
        if not item:
            continue
        kind = item[0]
        if kind == "set_motor" and len(item) >= 3:
            result.append(event("motor", int(item[1]), int(item[2])))
        elif kind == "set_led" and len(item) >= 3:
            result.append(event("led", int(item[1]), int(item[2])))
        elif kind == "delay" and len(item) >= 2:
            result.append(event("delay_ms", int(item[1])))
        elif kind == "read_ultrasonic":
            result.append(event("read_ultrasonic"))
        elif kind == "read_line_sensor" and len(item) >= 2:
            result.append(event("read_line", int(item[1])))
        elif kind == "read_touch" and len(item) >= 2:
            result.append(event("read_touch", int(item[1])))
        elif kind == "read_light" and len(item) >= 2:
            result.append(event("read_light", int(item[1])))
        elif kind == "read_color":
            result.append(event("read_color"))
        else:
            raise AssertionError(f"Unsupported runtime telemetry event: {item!r}")
    return tuple(result)


def compare_trace(
    actual: Iterable[TraceEvent],
    expected: Iterable[TraceEvent],
) -> tuple[bool, str]:
    actual_tuple = tuple(actual)
    expected_tuple = tuple(expected)
    if actual_tuple == expected_tuple:
        return True, ""
    max_len = max(len(actual_tuple), len(expected_tuple))
    lines = [
        f"trace length mismatch: actual={len(actual_tuple)} expected={len(expected_tuple)}"
    ]
    for index in range(max_len):
        actual_item = actual_tuple[index] if index < len(actual_tuple) else "<missing>"
        expected_item = expected_tuple[index] if index < len(expected_tuple) else "<missing>"
        if actual_item != expected_item:
            lines.append(
                f"first mismatch at index {index}: "
                f"actual={actual_item!r} expected={expected_item!r}"
            )
            break
    return False, "\n".join(lines)


def assert_trace(actual: Iterable[TraceEvent], expected: Iterable[TraceEvent]) -> None:
    ok, detail = compare_trace(actual, expected)
    if not ok:
        raise AssertionError(detail)
