# RSD-21.5 — RoboStudio + Compiler E2E

## Objective

Prove that the **production ZIP itself** is usable on a target machine: the
packaged RoboStudio application starts, invokes the application-owned compiler,
and produces compiler output from a Robosim Python program.

This gate is intentionally different from the legacy clean-machine portable
runtime acceptance. Python, PlatformIO, and device drivers remain target-machine
prerequisites; they are not copied into the production ZIP.

## System under test

```text
production ZIP
    ↓ extract to isolated temporary directory
RoboStudio executable from ZIP
    ↓ launch
RoboStudio startup
    ↓ compile command
Robosim Python sample
    ↓
compiler output / bytecode
```

The E2E runner never imports the repository's application implementation and
never uses the developer working tree as the application under test.

## Command contract

The runner accepts explicit command templates:

- `{app}` — the RoboStudio executable extracted from the ZIP
- `{source}` — the Robosim Python sample
- `{output}` — compiler output destination

Example shape:

```powershell
python -m tools.release_cli e2e <release.zip> `
  --source <sample.py> `
  --launch-command "<launcher> {app} --self-test" `
  --compile-command "<launcher> {app} --compile {source} --output {output}" `
  --report <e2e-report.json>
```

The command is executed with `shell=False`; command templates are parsed into
argument vectors rather than passed through a shell.

## Real product qualification

The compiler repository does not fabricate a RoboStudio executable. The real
RoboStudio build must supply a launch/compile command compatible with the
contract above. This keeps the test honest and allows the same gate to be used
with the actual production GUI/compiler integration.

## Evidence

The runner produces machine-readable evidence with schema:

```text
antechkids.robostudio.production-e2e / version 1
```

Evidence records:

- artifact name and SHA-256
- RoboStudio startup result
- compiler execution result
- compiler output existence and size
- captured stdout/stderr
- explicit assertion that host prerequisites are not packaged

## Regression

```powershell
python tests\rsd_21_5\run_rsd_21_5.py
```

The regression uses a deterministic test application only to validate the
runner contract. It does **not** claim that this fixture is the real RoboStudio
GUI. Real release qualification must use the production RoboStudio executable
from the assembled release artifact.
