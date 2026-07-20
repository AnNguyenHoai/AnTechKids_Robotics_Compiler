from pathlib import Path


class BuildArtifacts:

    def __init__(self, root):

        self.root = Path(root)

    @property
    def generated(self):

        return self.root / "generated"

    @property
    def sdk(self):

        return self.root / "sdk"