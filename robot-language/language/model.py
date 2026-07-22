"""
Robot Language Pure Model.

This module contains only data structure. No business logic.
"""


class RobotLanguage:
    """Pure data container for Robot Language specification."""

    def __init__(self, data: dict):
        self.data = data
        self.name = data["language"]["name"]
        self.version = data["language"]["version"]
        self.categories = data["categories"]