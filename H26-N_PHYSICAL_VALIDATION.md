# H26-N — Physical Validation Preflight

## Objective

Provide a deterministic preflight/evidence boundary before physical ESP32 validation. H26-N does **not** claim that a robot is physically tested when only host-side checks have run.

## Checks

The preflight consumes the H26-M deployment manifest and verifies:

1. deployment manifest and artifact integrity;
2. ESP32 target compatibility;
3. presence of the generated firmware program table;
4. `generated_program.h` byte-for-byte equality with the manifest's `program.h` artifact.

The generated artifact check requires both `generatedProgram` and `generatedProgramSize` so a partial firmware artifact cannot silently pass.

## Evidence model

The generated report distinguishes:

- **host-verifiable:** manifest, target/capability contract, artifact integrity, generated-program consistency;
- **physical-required:** device connection, motion execution, and sensor behavior.

A successful H26-N preflight therefore means **ready for physical test**, not **physical test passed**.

## Usage

```bash
python tests/h26_n/run_h26_n.py
```

For a real build manifest:

```bash
python tools/physical_validation.py build/<program>/deployment_manifest.json --report build/<program>/physical_validation.json
```

Physical execution evidence must be recorded separately after connecting the robot and exercising the intended program.
