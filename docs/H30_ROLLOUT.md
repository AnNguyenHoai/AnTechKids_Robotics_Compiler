# H30 Rollout

1. Merge after automated CI and physical two-robot acceptance.
2. Existing users start with an empty robot registry; first successful Discover populates it.
3. Existing discovery identity schema remains unchanged (`antechkids.robot.v1`, schema 1).
4. Existing single-robot OTA flow remains valid; H30 changes selection storage and discovery merge semantics, not the deployment protocol.
