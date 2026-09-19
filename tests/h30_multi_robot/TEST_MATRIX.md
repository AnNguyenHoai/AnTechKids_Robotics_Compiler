# H30 Test Matrix

| Contract | Automated | Physical |
| --- | --- | --- |
| Multiple robots persist across restart | Yes | Yes |
| Selection persists by `device_id` | Yes | Yes |
| Online state resets after restart | Yes | Yes |
| IP change does not duplicate robot | Yes | Yes |
| Missing robot becomes Offline, not deleted | Yes | Yes |
| OTA deploy requires current Online state | Source contract + regression | Yes |
| First-flash never chooses arbitrary existing robot | Yes | Yes |
| Full Windows production ZIP remains buildable | CI | N/A |
