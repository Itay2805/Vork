from typing import List, Dict, Optional
from vtypes import *
from vstmt import Stmt


class ModuleDecl:

    def __init__(self):
        self.name = 'main'
        self.functions = {}  # type: Dict[str, FunctionDecl]
        self.types = []  # type: List[VType]
        self.named_types = {}  # type: Dict[str, VType]

    def set_module_name(self, name):
        self.name = name

    def add_function(self, name, func):
        """
        :type name: str
        :type func: FunctionDecl
        """
        self.functions[name] = func

    def add_type(self, type, name=None):
        """
        :type type: VType
        :type name: str
        """

        if type in self.types:
            return self.types[self.types.index(type)]

        self.types.append(type)
        if name is not None:
            self.named_types[name] = type

        return type

    def _resolve_unresolved_type(self, unresolved):
        """
        :type unresolved: VUnresolvedType
        :rtype: VType
        """
        # get the type
        assert unresolved.type_name in self.named_types, f"Unknown type {unresolved.type_name}"
        t = self.named_types[unresolved.type_name]

        # Evolve mut
        if unresolved.mut != t.mut:
            t = t.copy()
            t.mut = unresolved.mut
            t = self.add_type(t)

        # return the type
        return t

    def _resolve_type(self, type):
        if isinstance(type, VRef) or isinstance(type, VArray) or isinstance(type, VOptional):
            if isinstance(type.type, VUnresolvedType):
                type.type = self._resolve_unresolved_type(type.type)
            else:
                self._resolve_type(type.type)
        elif isinstance(type, VMap):
            if isinstance(type.type0, VUnresolvedType):
                type.type0 = self._resolve_unresolved_type(type.type0)
            else:
                self._resolve_type(type.type0)
            if isinstance(type.type1, VUnresolvedType):
                type.type1 = self._resolve_unresolved_type(type.type1)
            else:
                self._resolve_type(type.type1)
        elif isinstance(type, VBool) or isinstance(type, VIntegerType):
            # Ignore
            return
        else:
            assert False, f"Unknown type type {type.__class__}"

    def resolve_types(self):
        # First go over sub types in types
        for t in self.types:
            self._resolve_type(t)

        for func in self.functions:
            func = self.functions[func]

            # resolve params
            for arg_name in func.params:
                param = func.params[arg_name]
                if isinstance(param, VUnresolvedType):
                    func.params[arg_name] = self._resolve_unresolved_type(param)

            # resolve return types
            for i in range(len(func.return_types)):
                ret_type = func.return_types[i]
                if isinstance(ret_type, VUnresolvedType):
                    func.return_types[i] = self._resolve_unresolved_type(ret_type)

        # now we should have all the functions fully resolved, so we are ready for type checking
        for func in self.functions:
            func = self.functions[func]
            func.root_scope.type_check(self, func.root_scope)


class StmtCompound(Stmt):

    def __init__(self, parent):
        """
        :type parent: FunctionScope or FunctionDecl
        """
        self.parent = parent
        self.code = []  # type: List[Stmt]

    def type_check(self, module, scope):
        for c in self.code:
            c.type_check(module, self)


class FunctionDecl:

    def __init__(self):
        self.pub = False
        self.params = {}  # type: Dict[str, VType]
        self.return_types = []  # type: List[VType]
        self.root_scope = StmtCompound(self)
        self.scope_stack = [self.root_scope]  # type: List[StmtCompound]

    def current_scope(self):
        return self.scope_stack[-1]

    def push_scope(self):
        current = self.current_scope()
        new_scope = StmtCompound(current)
        current.code.append(new_scope)
        self.scope_stack.append(new_scope)
        return new_scope

    def pop_scope(self):
        self.scope_stack.pop()
        return self.current_scope()

    def add_param(self, name, type):
        """
        :type name: str
        :type type: VType
        """
        assert name not in self.params, "Parameter with that name was already defined for this function"
        self.params[name] = type

    def add_return_type(self, type):
        """
        :type type: VType
        """
        self.return_types.append(type)
