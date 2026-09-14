# RSD-15 prerequisite flag regression

The compatibility contract is mode-aware:

- legacy bundled-runtime releases require `portable_python_required=true` and `bundled_platformio_required=true`;
- production releases require both flags to be `false` because Python and PlatformIO are target-machine prerequisites.

RSD-15 covers the legacy negative mutation by changing `portable_python_required` to `false` and requiring compatibility validation to reject it.
