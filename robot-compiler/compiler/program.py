from .instruction import Instruction
from .label import Label
from .patch import Patch

class Program:

    def __init__(self):
        self.instructions = []
        self.labels = []
        self.patches = []
        self.next_label_id = 0

    def emit(self, opcode, p1=0, p2=0, p3=0):
        self.instructions.append(
            Instruction(opcode, p1, p2, p3)
        )

    def new_label(self):

        label = Label(self.next_label_id)

        self.next_label_id += 1

        self.labels.append(label)

        return label

    def mark(self, label):

        if label.position is not None:

            raise Exception(
                "Label already marked."
            )

        label.position = len(self.instructions)

    def add_patch(
        self,
        instruction_index,
        label
    ):
        if label is None:

            raise Exception(
                "Invalid label."
            )
        self.patches.append(

            Patch(
                instruction_index,
                label
            )

        )

    def resolve_labels(self):

        for patch in self.patches:

            if patch.label.position is None:

                raise Exception(

                    f"Unresolved label {patch.label.id}"

                )

            instruction = self.instructions[
                patch.instruction_index
            ]

            instruction.p2 = patch.label.position

    def emit_label(
        self,
        label
    ):

        self.mark(label)

    def emit_jump(
        self,
        opcode,
        label
    ):

        instruction_index = len(self.instructions)

        self.emit(opcode)

        self.add_patch(
            instruction_index,
            label
        )

    def emit_jump_if_false(
        self,
        opcode,
        result,
        label
    ):

        instruction_index = len(self.instructions)

        self.emit(
            opcode,
            result
        )

        self.add_patch(
            instruction_index,
            label
        )