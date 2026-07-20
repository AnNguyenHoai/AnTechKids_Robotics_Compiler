

from .context import BuildContext


class Builder:

    def __init__(self):

        self.context = BuildContext()

        self.generators = []

        self.validators = []

    def register(
        self,
        generator
    ):

        self.generators.append(generator)

    def register_validator(self, validator):

        self.validators.append(
            validator
        )


    def validate(self):

        for validator in self.validators:

            print(f"Running {validator.name}...")

            validator.validate(
                self.context.language
            )

            print("PASS")
            print()

    def _print_summary(self):

        language = self.context.language

        print("=" * 60)
        print("Build Summary")
        print()

        print(f"Categories : {len(language.categories)}")
        print(f"Functions  : {sum(1 for _ in language.all_functions())}")
        print(f"Opcodes    : {sum(1 for _ in language.opcodes())}")
        print(f"Validators : {len(self.validators)}")
        print(f"Generators : {len(self.generators)}")
        print()

    def build(self):

        print()

        print("=" * 60)

        print("Robot Language Build")

        print("=" * 60)

        print()

        self.validate()
        for generator in self.generators:

            print(f"Running {generator.name}...")

            generator.generate(
                self.context
            )

            print("PASS")
            print()
        self._print_summary()

        print("=" * 60)

        print("BUILD SUCCESS")

        print("=" * 60)