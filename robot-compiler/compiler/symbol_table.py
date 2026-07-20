class SymbolTable:

    def __init__(self):

        self.variables = {}

        self.next_index = 0

    def allocate(self, name):

        if name not in self.variables:

            self.variables[name] = self.next_index
            self.next_index += 1

        return self.variables[name]

    def resolve(self, name):

        return self.variables[name]