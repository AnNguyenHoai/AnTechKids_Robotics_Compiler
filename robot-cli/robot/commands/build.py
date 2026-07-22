import click
import sys
from pathlib import Path
from ..core import config, utils

@click.command()
@click.option('--file', '-f', default='main.py', help='Source file to compile')
@click.option('--output', '-o', default=None, help='Output header file')
def build(file, output):
    click.echo(f"🔧 Building {file} ...")
    compiler_script = config.REPO_COMPILER / "main.py"
    if not compiler_script.exists():
        click.echo("❌ robot-compiler not found.", err=True)
        sys.exit(1)

    # Chuyển file thành đường dẫn tuyệt đối
    source_path = Path(file).resolve()
    if not source_path.exists():
        click.echo(f"❌ Source file '{file}' not found.", err=True)
        sys.exit(1)

    args = []
    if output:
        args.extend(['--output', str(Path(output).resolve())])
    # Truyền đường dẫn tuyệt đối cho compiler
    args.extend(['--file', str(source_path)])

    result = utils.run_script(compiler_script, args, capture=True)
    click.echo(result.stdout)
    if result.returncode != 0:
        click.echo(result.stderr, err=True)
        sys.exit(result.returncode)
    click.echo("✅ Build completed.")