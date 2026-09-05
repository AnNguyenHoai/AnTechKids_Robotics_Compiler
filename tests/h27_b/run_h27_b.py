from pathlib import Path
import sys


def main():
    repo_root = Path(__file__).resolve().parents[2]
    robostudio_dir = repo_root / "robostudio"
    sys.path.insert(0, str(robostudio_dir))

    # Reproduce the real test-runner import context: tests import RobotTab
    # directly rather than going through robostudio/main.py.
    from ui.robot_tab import RobotTab
    from services.bootstrap_config_service import BootstrapConfigService

    assert RobotTab is not None
    assert BootstrapConfigService is not None
    assert str(repo_root) in sys.path
    print("H27-B RoboStudio import-path regression: PASS")


if __name__ == "__main__":
    main()
