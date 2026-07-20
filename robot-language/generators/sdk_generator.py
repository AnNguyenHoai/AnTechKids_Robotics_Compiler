from pathlib import Path

from .base_generator import BaseGenerator


class SDKGenerator(BaseGenerator):

    name = "SDK Generator"

    def generate(self, context):
        language = context.language
        sdk_dir = context.sdk_dir

        for category_name, category in language.categories.items():
            if category_name == "internal":
                continue
            filename = sdk_dir / f"{category_name}.py"
            with open(filename, "w", encoding="utf8") as f:
                f.write('"""\nAUTO GENERATED FILE\n"""\n\n')
                for func in category["functions"]:
                    args = ", ".join(arg["name"] for arg in func["args"])
                    f.write(f"def {func['name']}({args}):\n    pass\n\n")