from pathlib import Path

from .base_generator import BaseGenerator


class SDKGenerator(BaseGenerator):

    name = "SDK Generator"

    def generate(
        self,
        context
    ):

        language = context.language
        sdk_dir = context.sdk_dir

        for category_name, category in language.categories.items():

            filename = sdk_dir / f"{category_name}.py"

            with open(
                filename,
                "w",
                encoding="utf8"
            ) as f:

                f.write('"""\n')
                f.write("AUTO GENERATED FILE\n")
                f.write('"""\n\n')

                for func in category["functions"]:

                    args = ", ".join(

                        arg["name"]

                        for arg in func["args"]

                    )

                    f.write(

                        f"def {func['name']}({args}):\n"

                    )

                    f.write(
                        "    pass\n\n"
                    )