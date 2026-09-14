# RSD-21.7 — Real Compiler Integration

## Objective

Make the **actual application-owned RoboSim compiler** part of the production RoboStudio artifact and prove that it can compile a representative program after the release ZIP is extracted away from the source repository.

## Production boundary

The production ZIP contains:

- `RoboStudio.exe`
- `RoboStudio.cmd`
- application-local DLL dependencies
- `compiler/main.py`
- the complete `compiler/` package required by `main.py`
- application resources
- release metadata and integrity evidence

Python is **not** bundled. The compiler is implemented in Python, so the target machine supplies the supported Python installation required to execute `compiler/main.py`. PlatformIO is also a target-machine prerequisite for hardware workflows and remains outside the ZIP.

## Compiler contract

The production compiler entry point is:

```text
compiler/main.py
```

It is the real source from `robot-compiler/main.py`, with its `compiler/` package and generated compiler assets copied into the production artifact.

The compiler is invoked with explicit arguments:

```powershell
python compiler\main.py --file <source.py> --output <output.h> --report <compile-report.json>
```

The release E2E command template supports:

- `{app}` — extracted RoboStudio executable;
- `{compiler}` — extracted `compiler/main.py`;
- `{source}` — external user source program;
- `{output}` — artifact-local compiler output.

Commands are executed without a shell and with the extracted RoboStudio directory as the working directory.

## What is proved

RSD-21.7 regression coverage proves that:

1. the real compiler source exists in the repository;
2. production assembly requires and packages the compiler root;
3. the compiler entry point and implementation package are present in the ZIP;
4. developer caches/virtual environments are not copied into the compiler payload;
5. the release remains free of bundled Python and PlatformIO;
6. the production ZIP validates normally;
7. the actual packaged compiler executes against a Robosim Python sample;
8. compiler output is produced from the extracted artifact; and
9. E2E evidence records the packaged compiler path.

The test does not pretend that a fixture RoboStudio executable is the real GUI. RoboStudio startup remains exercised as a process boundary while the compiler portion executes the **real compiler implementation**.

## Release build

The canonical production build now accepts the application-owned compiler explicitly:

```powershell
python -m tools.release_cli build `
  --executable <RoboStudio.exe> `
  --compiler-root <robot-compiler> `
  --runtime-resources <resources> `
  --version-file <VERSION> `
  --output <release-output>
```

`--runtime-bin` and `--runtime-platformio` are not production payload inputs.

## Regression

```powershell
python tests\rsd_21_7\run_rsd_21_7.py
```

Run the complete regression suite after this task:

```powershell
python run_all_tests.py
```
