from .error import CompilerError


class Scope:
    def __init__(self, parent=None, allocator=None):
        self.parent = parent
        self.variables = {}
        # Variable indices are program-global even when name lookup is lexical.
        # A child scope therefore allocates from the same counter as its root
        # allocator while keeping its own name bindings.
        self._allocator = allocator if allocator is not None else self
        self.next_index = 0

    def allocate(self, name):
        if name not in self.variables:
            self.variables[name] = self._allocator.next_index
            self._allocator.next_index += 1
        return self.variables[name]

    def resolve(self, name):
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.resolve(name)
        raise CompilerError(f"Variable '{name}' is not defined.")
