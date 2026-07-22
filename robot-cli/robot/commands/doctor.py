import click
import sys
import platform
from ..core import config, utils

@click.command()
def doctor():
    """Check system environment and repository health."""
    click.echo("🏥 Running doctor...")
    
    # Python version
    click.echo(f"🐍 Python: {sys.version}")
    
    # OS
    click.echo(f"💻 OS: {platform.system()} {platform.release()}")
    
    # Kiểm tra các repository
    repos = {
        "robot-compiler": config.REPO_COMPILER,
        "robot-language": config.REPO_LANGUAGE,
        "robot-platform": config.REPO_PLATFORM,
        "robot-frontend-robosim": config.REPO_FRONTEND,
        "robot-docs": config.REPO_DOCS,
    }
    all_ok = True
    for name, path in repos.items():
        if utils.check_repo_exists(path):
            click.echo(f"✅ {name}: OK")
        else:
            click.echo(f"❌ {name}: MISSING")
            all_ok = False
    
    # Kiểm tra file test
    if config.TEST_SCRIPT.exists():
        click.echo(f"✅ run_all_tests.py: OK")
    else:
        click.echo(f"❌ run_all_tests.py: MISSING")
        all_ok = False
    
    if all_ok:
        click.echo("✅ System looks healthy.")
    else:
        click.echo("⚠️ Some components are missing. Please check your installation.")
        sys.exit(1)