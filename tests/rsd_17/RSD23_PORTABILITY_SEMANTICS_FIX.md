# RSD-23 Portability Semantics Fix

RSD-23 changes runtime ownership: Python and PlatformIO are application-owned release payloads.

It does **not** redefine the existing `distribution-manifest.json` `portable` field. The field remains `false` under the established RSD-17 contract. The release can still be copied and deployed as a ZIP artifact; `portable` is not the runtime-ownership flag.

Runtime ownership is represented by the bundled paths and deployment-runtime manifest:

- `runtime/bin/python.exe`
- `runtime/platformio/`
- `runtime/platformio/deployment-runtime.json`

Keep the existing manifest schema/field semantics stable unless a dedicated release-contract task explicitly changes them.
