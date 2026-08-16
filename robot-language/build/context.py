from pathlib import Path
from language import RobotLanguage, LanguageQuery, LanguageLoader
from language.exceptions import SpecificationError


class BuildContext:
    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent
        self.spec_path = self.root / "specification" / "api.yaml"

        # Load language model
        self.language = LanguageLoader.load(self.spec_path)

        # Create query service
        self.query = LanguageQuery(self.language)

    @property
    def sdk_dir(self):
        return self.root / "robot"

    @property
    def generated_dir(self):
        return self.root / "generated"

    @property
    def docs_dir(self):
        return self.root / "docs"

    @property
    def compatibility_dir(self):
        return self.root.parent / "robot-docs" / "compatibility"