import re

from .base_validator import BaseValidator


class SemanticValidator(BaseValidator):

    name = "Semantic Validator"

    SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
    PASCAL_CASE = re.compile(
        r"^[A-Z][a-zA-Z0-9]*$"
    )

    def validate(self, language):

        self._validate_categories(language)
        self._validate_functions(language)
        self._validate_opcode_ids(language)
        self._validate_names(language)

    def _validate_categories(self, language):

        for category_name, category in language.all_categories():

            if not category["functions"]:

                raise ValueError(
                    f"Category '{category_name}' has no functions."
                )

    def _validate_functions(self, language):

        required_fields = (
            "name",
            "opcode",
            "opcode_id"
        )

        for _, _, function in language.all_functions():

            for field in required_fields:

                if field not in function:

                    raise ValueError(
                        f"Function '{function.get('name', '<unknown>')}' "
                        f"is missing field '{field}'."
                    )

    def _validate_opcode_ids(self, language):

        for opcode_id in language.opcode_ids():

            if opcode_id <= 0:

                raise ValueError(
                    f"Invalid Opcode ID: {opcode_id}"
                )

    def _validate_names(self, language):

        for category_name, _ in language.all_categories():

            self._validate_name(
                category_name,
                self.SNAKE_CASE,
                "Category"
            )

        for function_name in language.function_names():

            self._validate_name(
                function_name,
                self.SNAKE_CASE,
                "Function"
            )

        for opcode in language.opcodes():
            self._validate_name(
                opcode,
                self.PASCAL_CASE,
                "Opcode"
            )

    def _validate_name(
        self,
        value,
        pattern,
        object_name
    ):

        if not pattern.fullmatch(value):

            raise ValueError(
                f"Invalid {object_name} name: {value}"
            )