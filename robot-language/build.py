from build import Builder
from generators.registry_json_generator import RegistryJsonGenerator
from generators.opcode_header_generator import OpcodeHeaderGenerator

from generators import (
    SDKGenerator,
    RegistryGenerator,
    OpcodeGenerator,
    OpcodeJsonGenerator
)

from validation import (
    DuplicateValidator,
    SemanticValidator,
    ReferenceValidator
)

builder = Builder()

builder.register_validator(
    DuplicateValidator()
)

builder.register_validator(
    SemanticValidator()
)

builder.register_validator(
    ReferenceValidator()
)

builder.register(
    SDKGenerator()
)

builder.register(
    RegistryGenerator()
)

builder.register(
    RegistryJsonGenerator()
)

builder.register(
    OpcodeGenerator()
)

builder.register(
    OpcodeJsonGenerator()
)

builder.register(OpcodeHeaderGenerator())

builder.build()