from pathlib import Path
import yaml


class RobotLanguage:

    def __init__(self):

        root = Path(__file__).resolve().parent.parent

        spec_file = (
            root /
            "specification" /
            "api.yaml"
        )

        with open(spec_file, encoding="utf8") as f:

            self.data = yaml.safe_load(f)

    @property
    def name(self):

        return self.data["language"]["name"]

    @property
    def version(self):

        return self.data["language"]["version"]

    @property
    def categories(self):

        return self.data["categories"]

    def all_categories(self):

        return self.categories.items()

    def get_category(self, name):

        return self.categories[name]

    def all_functions(self):

        for category_name, category in self.categories.items():

            for function in category["functions"]:

                yield category_name, category, function

    def opcodes(self):

        for _, _, function in self.all_functions():

            yield function["opcode"]

    def opcode_ids(self):

        for _, _, function in self.all_functions():

            yield function["opcode_id"]

    def function_names(self):

        for _, _, function in self.all_functions():

            yield function["name"]

    def find_function(self, name):

        for _, _, function in self.all_functions():

            if function["name"] == name:

                return function

        return None

    def function_exists(self, name):

        return self.find_function(name) is not None
    
    def handler_of(self, category_name):

        return self.categories[category_name]["handler"]


    def module_of(self, category_name):

        return self.categories[category_name]["module"]    

    def handlers(self):

        for _, category in self.all_categories():

            yield category["handler"]

    def modules(self):

        for _, category in self.all_categories():

            yield category["module"]




