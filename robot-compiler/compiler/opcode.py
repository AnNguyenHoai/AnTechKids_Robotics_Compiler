import json
from pathlib import Path


class OpcodeTable:

    def __init__(self):

        opcode_file = (
            Path(__file__).resolve().parent.parent
            / "robot_spec"
            / "opcode.json"
        )

        with open(opcode_file, encoding="utf-8") as f:

            self.table = json.load(f)

        self.reverse = {}

        for name, value in self.table.items():

            self.reverse[value] = name

    def get(self, name):

        if name not in self.table:

            raise KeyError(

                f"Unknown opcode: {name}"

            )

        return self.table[name]

    def get_name(self, value):

        if value not in self.reverse:

            raise KeyError(

                f"Unknown opcode value: {value}"

            )

        return self.reverse[value]
    
    def exists(self, name):

        return name in self.table