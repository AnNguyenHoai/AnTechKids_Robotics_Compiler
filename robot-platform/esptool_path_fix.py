from pathlib import Path

Import("env")

# PlatformIO's Espressif builder normally invokes tool-esptoolpy/esptool.py
# directly through $PYTHONEXE. RoboStudio ships the Windows embeddable Python
# distribution with python310._pth isolation; in that mode Python does not add
# the external script directory to sys.path. The thin esptool.py wrapper then
# cannot import its sibling `esptool` package.
#
# Route esptool build/upload actions through a project-owned runner. The runner
# explicitly restores the tool package and _contrib directories to sys.path,
# preserving dependency closure without disabling embedded-Python isolation.
project_dir = Path(env.subst("$PROJECT_DIR")).resolve()
runner = project_dir / "esptool_runner.py"
if not runner.is_file():
    raise RuntimeError(f"Missing esptool runner: {runner}")

# ELF2BINCMD and ERASECMD reference $OBJCOPY lazily, so replacing OBJCOPY in a
# post script also fixes bootloader/application image generation.
env.Replace(OBJCOPY=str(runner))

# USB upload through esptool uses $UPLOADER. OTA keeps the framework's espota.py.
if env.subst("$UPLOAD_PROTOCOL").strip().lower() == "esptool":
    env.Replace(UPLOADER=str(runner))
