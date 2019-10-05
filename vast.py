from typing import List, Dict, Optional
from vtypes import *
from vstmt import *


class VModule:

    def __init__(self):
        self.name = 'main'
        self.types = []  # type: List[VType]
        self.identifiers = {}  # type: Dict[str, VFunction or VType]

    def set_module_name(self, name):
        self.name = name

    def add_function(self, name, func):
        """
        :type name: str
        :type func: VFunction
        """
        self.identifiers[name] = func

    def add_type(self, xtype, name=None):
        """
        :type xtype: VType
        :type name: str
        """

        # Don't add unresolved types to the list of types
        if not isinstance(xtype, VUnresolvedType):
            if xtype in self.types:
                xtype = self.types[self.types.index(xtype)]
            else:
                self.types.append(xtype)

        # Add to identifiers if needed
        if name is not None:
            self.identifiers[name] = xtype

        return xtype

    def resolve_unresolved_type(self, unresolved):
        """
        :type unresolved: VUnresolvedType
        :rtype: VType
        """
        # get the type
        assert unresolved.type_name in self.identifiers, f"Unknown type {unresolved.type_name}"
        t = self.identifiers[unresolved.type_name]
        assert isinstance(t, VType), f"{unresolved.type_name} is not a valid type"

        # If the type we got was not resolved yet, resolve it
        if isinstance(t, VUnresolvedType):
            t = self.resolve_unresolved_type(t)

        # Evolve mut
        if unresolved.mut != t.mut:
            t = t.copy()
            t.mut = unresolved.mut
            t = self.add_type(t)

        # return the type
        return t

    def _resolve_type(self, xtype):

        # Handle unresolved types
        if isinstance(xtype, VUnresolvedType):
            xtype = self.resolve_unresolved_type(xtype)

        # Handle types with one subtype
        elif isinstance(xtype, VRef) or isinstance(xtype, VArray) or isinstance(xtype, VOptional):
            xtype.type = self._resolve_type(xtype.type)

        # Handle type with two subtypes
        elif isinstance(xtype, VMap):
            xtype.type0 = self._resolve_type(xtype.type0)
            xtype.type1 = self._resolve_type(xtype.type1)

        # Function type resolving
        elif isinstance(xtype, VFunctionType):

            # Resolve the params
            for i in range(len(xtype.params)):
                param = xtype.params[i]
                if isinstance(param, VUnresolvedType):
                    xtype.params[i] = self._resolve_type(param)

            # resolve the arguments
            for i in range(len(xtype.return_types)):
                return_type = xtype.return_types[i]
                if isinstance(return_type, VUnresolvedType):
                    xtype.return_types[i] = self._resolve_type(return_type)

        # Handle builtin types
        elif isinstance(xtype, VBool) or isinstance(xtype, VIntegerType):
            pass

        # Unknown types will get an assert so we don't forget stuff
        else:
            assert False, f"Unknown type type {xtype.__class__}"

        return xtype

    def type_checking(self):
        # First go over sub types in types
        for t in self.types:
            self._resolve_type(t)

        # Make sure we don't have any unresolved identifier types (can come from type aliasing)
        for ident_name in self.identifiers:
            ident = self.identifiers[ident_name]
            if isinstance(ident, VUnresolvedType):
                self.identifiers[ident_name] = self._resolve_type(ident)

        # now we should have all the functions fully resolved,
        # so we are ready for type checking
        for ident in self.identifiers:
            ident = self.identifiers[ident]
            if isinstance(ident, VFunction):
                # Check the last statement is a return
                # TODO: Make this smarter
                if len(ident.root_scope.code) > 0:
                    last_stmt = ident.root_scope.code[-1]
                    if not isinstance(last_stmt, StmtReturn):
                        if len(ident.type.return_types) == 0:
                            # Just insert an empty return
                            ident.root_scope.code.append(StmtReturn([]))
                        else:
                            assert False, f"Missing return statement at end of function `{ident.name}`"
                else:
                    # No statements, insert a return if possible
                    if len(ident.type.return_types) == 0:
                        # Just insert an empty return
                        ident.root_scope.code.append(StmtReturn([]))
                    else:
                        assert False, f"Missing return statement at end of function `{ident.name}`"

                # Perform type checking on function
                ident.root_scope.type_check(self, ident.root_scope)


class StmtCompound(Stmt):

    def __init__(self, parent):
        """
        :type parent: StmtCompound or VFunction
        """
        self.parent = parent
        self.code = []  # type: List[Stmt]

    def type_check(self, module, scope):
        for c in self.code:
            c.type_check(module, self)

    def get_function(self):
        """
        :rtype: VFunction
        """
        if isinstance(self.parent, VFunction):
            return self.parent
        else:
            return self.parent.get_function()


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
