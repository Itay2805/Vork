from typing import List, Dict, Optional
from vtypes import VType
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


class StmtCompound(Stmt):

    def __init__(self, parent):
        """
        :type parent: FunctionScope or FunctionDecl
        """
        self.parent = parent
        self.code = []  # type: List[Stmt]


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
