# H30 Physical Acceptance Checklist

Use at least two robots on the same classroom Wi-Fi.

1. Power Robot A and Robot B; click **Discover**.
   - Both must appear Online with distinct `device_id` values.
2. Select Robot A, close RoboStudio, then reopen it.
   - Robot A remains selected by `device_id`.
   - Both known robots start Offline until a new Discover cycle.
3. Click **Discover** again.
   - Both return Online.
4. Power off Robot A and Discover again.
   - Robot A remains listed Offline.
   - Robot B remains Online.
   - Robot A remains selected if it was selected before the scan.
   - **RUN ON ROBOT** is disabled while Robot A is Offline.
5. Power Robot A back on and Discover again.
   - Robot A returns Online under the same `device_id`, even if DHCP changed its IP.
   - No duplicate Robot A entry appears.
6. Select Robot B and perform OTA deployment.
   - Verification must return Robot B's exact `device_id`.
   - Robot A must not be treated as the deployment target.
7. First-flash a new Robot C while A and B are online.
   - RoboStudio may auto-bind C only if exactly one new `device_id` appears after flash.
   - In ambiguous discovery, RoboStudio must ask for manual Discover/selection rather than choosing the first robot.
