import os
import sys
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main():
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "robostudio"))

    from PySide6.QtWidgets import QApplication
    from ui.robot_tab import RobotTab

    app = QApplication.instance() or QApplication([])
    tab = RobotTab(lambda: "print('test')")

    log = "\n".join(f"log line {index}" for index in range(5000))
    tab.set_logs(log)

    assert tab.output_label.toPlainText() == log
    assert tab.output_label.isReadOnly()
    assert tab.output_label.lineWrapMode() == tab.output_label.LineWrapMode.NoWrap
    assert tab.clear_logs_button is not None
    assert tab.copy_logs_button is not None

    tab.clear_logs()
    assert tab.output_label.toPlainText() == ""

    tab.set_logs(log)
    tab.copy_logs()
    assert app.clipboard().text() == log

    tab.close()
    print("RoboStudio deployment log viewer regression: PASS")


if __name__ == "__main__":
    main()
