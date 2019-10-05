from typing import List, Dict, Optional
from vtypes import *
from vstmt import Stmt


class ModuleDecl:

    def __init__(self):
        self.name = 'main'
        self.functions = {}  # type: Dict[str, VFunction]
        self.types = []  # type: List[VType]
        self.named_types = {}  # type: Dict[str, VType]

    def set_module_name(self, name):
        self.name = name

    def add_function(self, name, func):
        """
        :type name: str
        :type func: VFunction
        """
        self.functions[name] = func

    def add_type(self, xtype, name=None):
        """
        :type xtype: VType
        :type name: str
        """

        if xtype in self.types:
            xtype = self.types[self.types.index(xtype)]
        else:
            self.types.append(xtype)

        if name is not None:
            self.named_types[name] = xtype

        return xtype

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

        # Function type resolving
        elif isinstance(type, VFunctionType):

            # Resolve the params
            for i in range(len(type.params)):
                param = type.params[i]
                if isinstance(param, VUnresolvedType):
                    type.params[i] = self._resolve_unresolved_type(param)

            # resolve the arguments
            for i in range(len(type.return_types)):
                return_type = type.return_types[i]
                if isinstance(return_type, VUnresolvedType):
                    type.return_types[i] = self._resolve_unresolved_type(return_type)

        elif isinstance(type, VBool) or isinstance(type, VIntegerType):
            # Ignore
            return
        else:
            assert False, f"Unknown type type {type.__class__}"

    def resolve_types(self):
        # First go over sub types in types
        for t in self.types:
            self._resolve_type(t)

        # now we should have all the functions fully resolved, so we are ready for type checking
        for func in self.functions:
            func = self.functions[func]
            func.root_scope.type_check(self, func.root_scope)


class StmtCompound(Stmt):

    def __init__(self, parent):
        """
        :type parent: FunctionScope or VFunction
        """
        self.parent = parent
        self.code = []  # type: List[Stmt]

    def type_check(self, module, scope):
        for c in self.code:
            c.type_check(module, self)


class VFunction:

    def __init__(self):
        self.name = ''
        self.pub = False
        self.type = VFunctionType(False)
        self.param_names = []  # type: List[str]
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
        assert name not in self.param_names
        self.param_names.append(name)
        self.type.add_param(type)

    def add_return_type(self, type):
        """
        :type type: VType
        """
        self.type.return_types.append(type)

    def __str__(self):
        params = ', '.join([f'{self.param_names[i]} {self.type.params[i]}' for i in range(len(self.param_names))])
        return_types = ', '.join([f'{arg}' for arg in self.type.return_types])
        if len(self.type.return_types) > 1:
            return_types = f'({return_types})'
        return f'fn {self.name} ({params}) {return_types}'
