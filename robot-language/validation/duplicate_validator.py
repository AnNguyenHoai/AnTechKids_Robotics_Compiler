from .base_validator import BaseValidator


class DuplicateValidator(BaseValidator):

    name = "Duplicate Validator"

    def validate(self, language):

        self._check(
            language.function_names(),
            "Function"
        )

        self._check(
            language.opcodes(),
            "Opcode"
        )

        self._check(
            language.opcode_ids(),
            "Opcode ID"
        )

        self._check(
            language.handlers(),
            "Handler"
        )

        self._check(
            language.modules(),
            "Module"
        )

    def _check(
        self,
        values,
        object_name
    ):

        visited = set()

        for value in values:

            if value in visited:

                raise ValueError(
                    f"Duplicate {object_name}: {value}"
                )

            visited.add(value)