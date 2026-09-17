# RSD-20 Runtime Build Fixture Compatibility

RSD-23 made application-owned Python and PlatformIO explicit inputs to production release assembly.

The RSD-20 CLI regression fixture already creates those assets under `distribution/runtime`, but its `release_cli build` invocation omitted the corresponding `--runtime-bin` and `--runtime-platformio` arguments. The fix passes the fixture-owned runtime paths explicitly so RSD-20 exercises the current production release contract instead of relying on deprecated implicit inputs.
