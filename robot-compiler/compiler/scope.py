class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.variables = {}
        self.next_index = 0

    def allocate(self, name):
        if name not in self.variables:
            self.variables[name] = self.next_index
            self.next_index += 1
        return self.variables[name]

    def resolve(self, name):
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.resolve(name)
        raise KeyError(f"Variable '{name}' not found")