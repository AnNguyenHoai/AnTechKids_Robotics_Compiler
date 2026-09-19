# H30 Implementation Notes

- Stable key: H27 `device_id` derived from ESP32 eFuse MAC.
- Durable state: last-known robot identity snapshot + `last_seen_utc` + `selected_device_id`.
- Ephemeral state: `online` is never trusted after application restart.
- Discovery semantics: merge into registry; never replace the registry with only the latest scan.
- Deployment semantics: selected robot must be Online + Ready + OTA-capable before Run is enabled.
- First-flash safety: auto-bind only one newly appeared `device_id`; never use list position.
- Secrets: Wi-Fi/OTA credentials are not added to robot registry persistence.
