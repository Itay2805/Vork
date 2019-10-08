from vtypes import *


########################################################################
# Basic AST types
########################################################################


class Expr:

    def resolve_type(self, module, scope):
        """
        :type module: VModule
        :type scope: StmtCompound
        :rtype: VType
        """
        raise NotImplementedError


class Stmt:

    def type_check(self, module, scope):
        """
        :type module: VModule
        :type scope: StmtCompound
        """
        raise NotImplementedError


class StmtCompound(Stmt):

    def __init__(self, parent):
        """
        :type parent: StmtCompound or VFunction
        """
        self.parent = parent
        self.variables = {}  # type: Dict[str, VVariable]
        self.code = []  # type: List[Stmt]

    def type_check(self, module, scope):
        for c in self.code:
            c.type_check(module, self)

    def get_identifier(self, name):
        if name in self.variables:
            return self.variables[name]
        return self.parent.get_identifier(name)

    def add_variable(self, name, xtype):
        """
        :type name: str
        :type xtype: VType
        """
        assert name not in self.variables, f"Already got variable with name `{name}`"
        self.variables[name] = VVariable(name, xtype)

    def get_function(self):
        """
        :rtype: VFunction
        """
        if isinstance(self.parent, VFunction):
            return self.parent
        else:
            return self.parent.get_function()


########################################################################
# Important objects
########################################################################

class VModule:

    def __init__(self):
        self.name = 'main'
        self.types = []  # type: List[VType]
        self.identifiers = {}  # type: Dict[str, VFunction or VType]
        self.type_checked = False

    def set_module_name(self, name):
        self.name = name

    def get_identifier(self, name):
        # Check in the identifiers
        if name in self.identifiers:
            return self.identifiers[name]

        # If there is builtin fall back to that
        if 'builtin' in self.identifiers and self.identifiers['builtin'] != self:
            return self.identifiers['builtin'].get_identifier(name)

        # None found
        return None

    def add_function(self, name, func):
        """
        :type name: str
        :type func: VFunction
        """
        # TODO: I think function overloading is a thing, so we need to somehow take care of that
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
        t = self.get_identifier(unresolved.type_name)
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
            for i in range(len(xtype.param_types)):
                param = xtype.param_types[i]
                if isinstance(param, VUnresolvedType):
                    xtype.param_types[i] = self._resolve_type(param)

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
        from vstmt import StmtReturn

        # This should prevent us from type checking multiple times the same thing
        # and prevent cyclic depends
        if self.type_checked:
            return
        self.type_checked = True

        # First go over sub types in types
        for t in self.types:
            self._resolve_type(t)

        # Make sure we don't have any unresolved identifier types (can come from type aliasing)
        for ident_name in self.identifiers:
            ident = self.identifiers[ident_name]

            # resolve unresolved types
            if isinstance(ident, VUnresolvedType):
                self.identifiers[ident_name] = self._resolve_type(ident)

            # do the module's type checking
            elif isinstance(ident, VModule):
                ident.type_checking()

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

    def add_builtin_function(self, func):
        """
        :type func: VBuiltinFunction
        """
        func.type = self.add_type(func.type)
        self.identifiers[func.name] = func

class VVariable:

    def __init__(self, name, type):
        """
        :type name: str`
        :type type: VType
        """
        self.name = name
        self.type = type

    def __str__(self):
        return f'{self.name} {self.type}'


class VBuiltinFunction:

    def __init__(self, name, params, return_types):
        self.name = name

        self.type = VFunctionType(False)
        for p in params:
            self.type.add_param(VUnresolvedType(False, p))
        self.type.return_types = [VUnresolvedType(False, p) for p in return_types]


class VFunction:

    def __init__(self, module):
        self.name = ''
        self.module = module  # type: VModule
        self.pub = False
        self.type = VFunctionType(False)
        self.param_names = []  # type: List[str]
        self.root_scope = StmtCompound(self)
        self.scope_stack = [self.root_scope]  # type: List[StmtCompound]

    def get_identifier(self, name):
        if name in self.param_names:
            index = self.param_names.index(name)
            return VVariable(self.param_names[index], self.type.param_types[index])
        return self.module.get_identifier(name)

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
        params = ', '.join([f'{self.param_names[i]} {self.type.param_types[i]}' for i in range(len(self.param_names))])
        return_types = ', '.join([f'{arg}' for arg in self.type.return_types])
        if len(self.type.return_types) > 1:
            return_types = f'({return_types})'
        return f'fn {self.name} ({params}) {return_types}'
