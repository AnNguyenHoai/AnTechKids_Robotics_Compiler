from .base_validator import BaseValidator
from language.exceptions import DuplicateError


class DuplicateValidator(BaseValidator):
    name = "Duplicate Validator"

    def validate(self, query):
        self._check(query.function_names(), "Function")
        self._check(query.opcodes(), "Opcode")
        self._check(query.opcode_ids(), "Opcode ID")
        self._check(query.handlers(), "Handler")
        self._check(query.modules(), "Module")

    def _check(self, values, object_name):
        visited = set()
        for value in values:
            if value in visited:
                raise DuplicateError(f"Duplicate {object_name}: {value}")
            visited.add(value)