from pathlib import Path

from language import RobotLanguage


class BuildContext:

    def __init__(self):

        self.root = Path(__file__).resolve().parent.parent

        self.language = RobotLanguage()

    @property
    def sdk_dir(self):

        return self.root / "sdk"

    @property
    def generated_dir(self):

        return self.root / "generated"

    @property
    def docs_dir(self):

        return self.root / "docs"