from .error import CompilerError


class Scope:
    def __init__(self, parent=None, allocator=None):
        self.parent = parent
        self.variables = {}
        self.global_names = set()
        # Variable indices are program-global even when name lookup is lexical.
        # A child scope therefore allocates from the same counter as its root
        # allocator while keeping its own name bindings.
        self._allocator = allocator if allocator is not None else self
        self.next_index = 0

    def _root(self):
        scope = self
        while scope.parent is not None:
            scope = scope.parent
        return scope

    def declare_global(self, name):
        if self.parent is None:
            return
        if name in self.variables:
            raise CompilerError(
                f"Variable '{name}' is assigned before global declaration."
            )
        self.global_names.add(name)

    def allocate(self, name):
        if name in self.global_names:
            return self._root().allocate(name)
        if name not in self.variables:
            self.variables[name] = self._allocator.next_index
            self._allocator.next_index += 1
        return self.variables[name]

    def resolve(self, name):
        if name in self.global_names:
            return self._root().resolve(name)
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.resolve(name)
        raise CompilerError(f"Variable '{name}' is not defined.")
