from vtypes import *


########################################################################
# Basic AST types
########################################################################


class Expr:

    def __init__(self, report):
        self.report = report

    def resolve_type(self, module, scope):
        """
        Will attempt to resovle the return
        type of the expression

        can be a list for multiple return

        :type module: VModule
        :type scope: StmtCompound
        :rtype: VType or List[VType]
        """
        raise NotImplementedError

    def is_mut(self, module, scope):
        """
        Will check if the expression returns a mutable result
        :type module: VModule
        :type scope: StmtCompound
        :rtype: bool
        """
        return NotImplemented


class Stmt:

    def __init__(self, report):
        self.report = report

    def type_check(self, module, scope):
        """
        :type module: VModule
        :type scope: StmtCompound
        """
        raise NotImplementedError


class StmtCompound(Stmt):

    def __init__(self, parent, report):
        """
        :type parent: StmtCompound or VFunction
        """
        super(StmtCompound, self).__init__(report)
        self.parent = parent
        self.variables = {}  # type: Dict[str, VVariable]
        self.code = []  # type: List[Stmt]
        self.reporter = None
        self.line_start = 0
        self.line_end = 0

    def fix_children(self):
        assert self.parent is not None

        from vstmt import StmtIf, StmtFor, StmtForeach
        for c in self.code:
            if isinstance(c, StmtCompound):
                c.parent = self
                c.fix_children()
            elif isinstance(c, StmtIf):
                c.stmts_true.parent = self
                c.stmts_true.fix_children()
                if c.stmts_false is not None:
                    c.stmts_false.parent = self
                    c.stmts_false.fix_children()
            elif isinstance(c, StmtForeach) or isinstance(c, StmtFor):
                c.stmts.parent = self
                c.stmts.fix_children()

    def type_check(self, module, scope):
        from vexpr import TypeCheckError
        is_good = True
        for c in self.code:
            try:
                ret = c.type_check(module, self)
                if ret is not None and not ret:
                    is_good = False
            except TypeCheckError as e:
                is_good = False
                e.report('error', e.msg, e.func)

        return is_good

    def get_identifier(self, name):
        if name in self.variables:
            return self.variables[name]
        return self.parent.get_identifier(name)

    def add_variable(self, name, mut, xtype):
        """
        :type name: str
        :type mut: bool
        :type xtype: VType
        """
        if name in self.variables:
            return False

        self.variables[name] = VVariable(mut, name, xtype)
        return True

    def get_function(self):
        """
        :rtype: VFunction
        """
        if isinstance(self.parent, VFunction):
            return self.parent
        else:
            return self.parent.get_function()

    def __str__(self):
        return "[" + ','.join([str(c) for c in self.code]) + "]"


########################################################################
# Important objects
########################################################################

class VModule:

    def __init__(self):
        from vworkspace import VWorkspace
        self.name = 'main'
        self.ran_init = False
        self.types = []  # type: List[VType]
        self.identifiers = {'C': {}}  # type: Dict[str, VFunction or VType]
        self.type_checked = False
        self.is_good = True
        self.workspace = None  # type: VWorkspace

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

    def add_function(self, name, func, report):
        """
        :type name: str
        :type func: VFunction
        """
        # TODO: I think function overloading is a thing, so we need to somehow take care of that
        if name in self.identifiers:
            report('error', f'redefinition of `{name}`')
        else:
            self.identifiers[name] = func

    def add_type(self, xtype, report=None, name=None):
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
            assert report is not None
            if name in self.identifiers:
                report('error', f'redefinition of `{name}`')
            else:
                self.identifiers[name] = xtype

        return xtype

    def resolve_unresolved_type(self, unresolved):
        """
        :type unresolved: VUnresolvedType
        :rtype: VType
        """
        # get the type
        if unresolved.module is None:
            unresolved.module = self
        t = unresolved.module.get_identifier(unresolved.type_name)

        assert isinstance(t, VType), f"`{unresolved.type_name}` is not a valid type"

        # If the type we got was not resolved yet, resolve it
        if isinstance(t, VUnresolvedType):
            t = self.resolve_unresolved_type(t)

        # return the type
        return t

    def resolve_type(self, xtype):

        # Handle unresolved types
        if isinstance(xtype, VUnresolvedType):
            xtype = self.resolve_unresolved_type(xtype)

        # Handle types with one subtype
        elif isinstance(xtype, VRef) or isinstance(xtype, VArray) or isinstance(xtype, VOptional):
            xtype.module = self.workspace.load_module('builtin')
            xtype.xtype = self.resolve_type(xtype.xtype)

        # Handle type with two subtypes
        elif isinstance(xtype, VMap):
            xtype.module = self.workspace.load_module('builtin')
            xtype.key_type = self.resolve_type(xtype.key_type)
            xtype.value_type = self.resolve_type(xtype.value_type)

        # Function type resolving
        elif isinstance(xtype, VFunctionType):
            if xtype.module is None:
                xtype.module = self

            # Resolve the params
            for i in range(len(xtype.param_types)):
                param = xtype.param_types[i]
                xtype.param_types[i] = xtype.module.resolve_type(param[0]), param[1]

            # resolve the arguments
            for i in range(len(xtype.return_types)):
                return_type = xtype.return_types[i]
                xtype.return_types[i] = xtype.module.resolve_type(return_type)

        # Handle builtin types
        elif isinstance(xtype, VBool) or isinstance(xtype, VIntegerType):
            pass

        # Handle structs
        elif isinstance(xtype, VStructType):
            if xtype.module is None:
                xtype.module = self

            # Resolve the actual embedded type
            if xtype.embedded is not None:
                xtype.embedded = xtype.module.resolve_type(xtype.embedded)

            # Resole the fields of the struct
            for i in range(len(xtype.fields)):
                field = xtype.fields[i]
                field.xtype = xtype.module.resolve_type(field.xtype)

            # Resolve the methods of the struct
            for name in xtype.methods:
                method = xtype.methods[name]
                method.type = xtype.module.resolve_type(method.type)

        # Unknown types will get an assert so we don't forget stuff
        else:
            assert False, f"Unknown type type {xtype.__class__}"

        return self.workspace.add_type(self.add_type(xtype))

    def type_checking(self):
        from vstmt import StmtReturn

        if self.type_checked:
            return self.is_good
        self.type_checked = True

        is_good = True

        # We start by doing type resolving on all the module level stuff
        for name in self.identifiers:
            ident = self.identifiers[name]

            # If it is a function just resolve the signature also will
            # add the parameters as variables in the root scope
            if isinstance(ident, VFunction):
                ident.type = self.resolve_type(ident.type)
                for i in range(len(ident.param_names)):
                    ident.root_scope.add_variable(ident.param_names[i], ident.type.param_types[i][1], ident.type.param_types[i][0])

            # For builtin functions only need to resovle the signature
            elif isinstance(ident, VInteropFunction):
                ident.type = self.resolve_type(ident.type)

            # If this is a type make sure it is resolved
            elif isinstance(ident, VType):
                self.identifiers[name] = self.resolve_type(ident)

            # TODO: Why are we not using VStruct?

            # For imported modules do type checking
            elif isinstance(ident, VModule):
                if not ident.type_checking():
                    is_good = False

            # Interops are simply stored in a dict
            # because this will only have types it should be fine
            elif isinstance(ident, dict):
                for name in ident:
                    ident[name].type = self.resolve_type(ident[name].type)

            elif isinstance(ident, VConstant):
                from vexpr import TypeCheckError

                try:
                    ident.type_check(self, self._dummy_scope())
                except TypeCheckError as e:
                    e.report('error', e.msg)

            else:
                assert False

        # Now the module level should be fine, we can do type checking on the
        # statement level
        for name in self.identifiers:
            ident = self.identifiers[name]
            if isinstance(ident, VFunction):
                if not ident.type_check(self):
                    is_good = False

            elif isinstance(ident, VModule):
                if not ident.type_checking():
                    is_good = False

            # TODO: Why are we not using VStruct

            elif isinstance(ident, VStructType):
                for method in ident.methods:
                    if not ident.methods[method].type_check(self):
                        is_good = False

        self.is_good = is_good
        return is_good

    def _dummy_scope(self):
        """
        Dummy for type checking
        """
        module = self

        class Dummy:

            def get_identifier(self, name):
                return module.get_identifier(name)

            def get_function(self):
                class DummyFunc:
                    def __init__(self):
                        self.name = None
                return DummyFunc()

        return Dummy()


class VVariable:

    def __init__(self, mut, name, type):
        """
        :type mut: bool
        :type name: str
        :type type: VType
        """
        self.mut = mut
        self.name = name
        self.type = type

    def __str__(self):
        return f'{self.name} {self.type}'


class VConstant:

    def __init__(self, name, expr, report):
        """
        :type name: str
        :type expr: Expr
        """
        self.name = name
        self.expr = expr
        self.report = report
        self._type = None

    def get_type(self):
        assert self._type is not None
        return self._type

    def type_check(self, module, scope):
        self._type = self.expr.resolve_type(module, scope)

    def __str__(self):
        return f'const {self.name} = {self.expr}'


class VInteropFunction:

    def __init__(self, type, name):
        self.interop_type = type
        self.name = name
        self.type = VFunctionType()

    def add_param(self, mut, xtype):
        """
        :type name: str
        :type mut: bool
        :type xtype: VType
        """
        self.type.add_param(mut, xtype)

    def add_return_type(self, type):
        """
        :type type: VType
        """
        self.type.add_return_type(type)

    def __str__(self):
        params = ', '.join([f'{"mut " if param[1] else ""}{param[0]}' for param in self.type.param_types])
        return_types = ', '.join(map(str, self.type.return_types))
        if len(self.type.return_types) > 1:
            return_types = f'({return_types})'
        return f'fn C.{self.name} ({params}) {return_types}'


class VFunction:

    def __init__(self, report):
        self.name = ''
        self.report = report
        self.pub = False
        self.type = VFunctionType()
        self.param_names = []  # type: List[str]
        self.root_scope = StmtCompound(self, report)
        self.scope_stack = [self.root_scope]  # type: List[StmtCompound]

    def get_module(self):
        return self.type.module

    def get_identifier(self, name):
        if name in self.param_names:
            index = self.param_names.index(name)
            return VVariable(self.type.param_types[index][1], self.param_names[index], self.type.param_types[index][0])
        return self.get_module().get_identifier(name)

    def add_param(self, name, mut, xtype):
        """
        :type name: str
        :type mut: bool
        :type xtype: VType
        """
        assert name not in self.param_names
        self.param_names.append(name)
        self.type.add_param(mut, xtype)

    def add_return_type(self, type):
        """
        :type type: VType
        """
        self.type.add_return_type(type)

    def type_check(self, module):
        from vstmt import StmtReturn

        # Do normal type checking
        if not self.root_scope.type_check(module, self.root_scope):
            return False

        # init functions must be fn() and can not be public
        if self.name == 'init':
            if len(self.type.return_types) != 0:
                self.report('error', 'init function cannot have return types')
                return False
            elif len(self.type.param_types) != 0:
                self.report('error', 'init function cannot have param types')
                return False
            elif self.pub:
                self.report('error', 'init function cannot be public')
                return False

        # TODO: A bit more advanced return checks

        # Check return types
        if len(self.type.return_types) > 0:

            found = False
            for stmt in self.root_scope.code:
                if isinstance(stmt, StmtReturn):
                    found = True
                    break
            if not found:
                self.root_scope.reporter.reporter(self.root_scope.line_end, 1, self.root_scope.line_end + 1)('error', 'control reaches end of non-void function', func=self.name)

        elif len(self.root_scope.code) == 0 or not isinstance(self.root_scope.code[-1], StmtReturn):
            # Insert a return because this function has no return arguments and last item is not a return
            self.root_scope.code.append(StmtReturn([], None))

        return True

    def __str__(self):
        params = ', '.join([f'{self.param_names[i]} {"mut " if self.type.param_types[i][1] else ""}{self.type.param_types[i][0]}' for i in range(len(self.param_names))])
        return_types = ', '.join(map(str, self.type.return_types))
        if len(self.type.return_types) > 1:
            return_types = f'({return_types})'
        return f'fn {self.name} ({params}) {return_types}'


class VStruct:

    def __init__(self, pub, name, struct_type, report):
        """
        :type name: str
        :type struct_type: VStructType
        """
        self.name = name
        self.pub = pub
        self.type = struct_type
        self.report = report

    def get_module(self):
        return self.type.module

    def get_field(self, name):
        return self.type.get_field(name)
