import re
from .base_validator import BaseValidator
from language.exceptions import ValidationError


class SemanticValidator(BaseValidator):
    name = "Semantic Validator"

    SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
    PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")

    def validate(self, query):
        self._validate_categories(query)
        self._validate_functions(query)
        self._validate_opcode_ids(query)
        self._validate_names(query)

    def _validate_categories(self, query):
        for cat_name, cat in query.categories().items():
            if not cat.get("functions"):
                raise ValidationError(f"Category '{cat_name}' has no functions.")

    def _validate_functions(self, query):
        required_fields = ("name", "opcode", "opcode_id")
        for _, _, func in query.functions():
            for field in required_fields:
                if field not in func:
                    raise ValidationError(
                        f"Function '{func.get('name', '<unknown>')}' missing field '{field}'."
                    )

    def _validate_opcode_ids(self, query):
        for opcode_id in query.opcode_ids():
            if opcode_id <= 0:
                raise ValidationError(f"Invalid Opcode ID: {opcode_id}")

    def _validate_names(self, query):
        # Category and function names: snake_case, skip internal
        for cat_name, cat in query.categories().items():
            if cat_name == "internal":
                continue
            self._validate_name(cat_name, self.SNAKE_CASE, "Category")
            for func in cat.get("functions", []):
                self._validate_name(func["name"], self.SNAKE_CASE, "Function")

        # Opcode names: PascalCase
        for opcode in query.opcodes():
            self._validate_name(opcode, self.PASCAL_CASE, "Opcode")

    def _validate_name(self, value, pattern, object_name):
        if not pattern.fullmatch(value):
            raise ValidationError(f"Invalid {object_name} name: {value}")