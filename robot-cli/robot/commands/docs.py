import click
import sys
from pathlib import Path
from ..core import config, utils

@click.command()
@click.option('--output', '-o', default=None, help='Output directory for documentation (default: robot-docs/generated)')
def docs(output):
    """Generate documentation from specification."""
    click.echo("📝 Generating documentation...")
    # Chạy robot-language build (để sinh docs)
    build_script = config.REPO_LANGUAGE / "build.py"
    if not build_script.exists():
        click.echo("❌ robot-language/build.py not found.", err=True)
        sys.exit(1)

    # Chạy build để kích hoạt DocGenerator
    result = utils.run_script(build_script, capture=True)
    if result.returncode != 0:
        click.echo(result.stderr, err=True)
        sys.exit(result.returncode)

    # Nếu có output tùy chỉnh, copy docs đến đó (optional)
    if output:
        src = config.ROOT / "robot-docs" / "generated"
        if src.exists():
            dst = Path(output)
            dst.mkdir(parents=True, exist_ok=True)
            for f in src.glob("*.md"):
                shutil.copy2(f, dst / f.name)
            click.echo(f"✅ Documentation copied to {dst}")
        else:
            click.echo("⚠️ No generated docs found.", err=True)
    else:
        click.echo("✅ Documentation generated in robot-docs/generated/")