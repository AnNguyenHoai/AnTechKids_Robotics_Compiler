import click
import subprocess
import sys
from pathlib import Path
from ..core import config, utils

@click.command()
@click.option('--file', '-f', default='main.py', help='Source file to compile')
@click.option('--output', '-o', default=None, help='Output header file')
@click.option('--build-dir', help='Build directory')
@click.option('--copy', is_flag=True, help='Copy header to robot-platform after build')
def build(file, output, build_dir, copy):
    click.echo(f"[BUILD] Building {file} ...")
    build_script = config.ROOT / "tools" / "build.py"
    if not build_script.exists():
        click.echo("ERROR: tools/build.py not found.", err=True)
        sys.exit(1)

    cmd = [sys.executable, str(build_script), "--input", str(Path(file).resolve())]
    if output:
        cmd.extend(["--output", str(Path(output).resolve())])
    if build_dir:
        cmd.extend(["--build-dir", str(Path(build_dir).resolve())])
    if copy:
        cmd.append("--copy")

    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        sys.exit(result.returncode)
    click.echo("[OK] Build completed.")