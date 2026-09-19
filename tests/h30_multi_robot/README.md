# H30 Multi-Robot Regression

This suite locks the persistent multi-robot contract:

- registry keyed by stable `device_id`;
- multiple robots persist across restart;
- online state does not persist across restart;
- selected robot persists by `device_id`;
- IP changes update the same robot instead of creating duplicates;
- successful discovery retains absent robots as Offline;
- first-flash never binds an arbitrary existing LAN robot;
- Robot tab exposes Online/Offline state and only deploys to a currently online selection.
