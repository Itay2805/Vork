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
        for c in self.code:
            if isinstance(c, StmtCompound):
                c.parent = self
                c.fix_children()

    def type_check(self, module, scope):
        from vexpr import TypeCheckError
        got_error = False
        for c in self.code:
            try:
                ret = c.type_check(module, self)
                if ret is not None and ret:
                    got_error = True
            except TypeCheckError as e:
                got_error = True
                e.report('error', e.msg, e.func)
        return got_error

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
        assert name not in self.variables, f"Already got variable with name `{name}`"
        self.variables[name] = VVariable(mut, name, xtype)

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
        self.types = []  # type: List[VType]
        self.identifiers = {}  # type: Dict[str, VFunction or VType]
        self.type_checked = False
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

            if xtype.embedded is not None:
                xtype.embedded = xtype.module.resolve_type(xtype.embedded)

            for i in range(len(xtype.fields)):
                field = xtype.fields[i]
                field.xtype = xtype.module.resolve_type(field.xtype)

            # TODO: Check embedded field
            # Make sure all the types seem good
            # if xtype.embedded is not None:
            #     for field in xtype.fields:
            #         assert xtype.embedded.get_field(field[0]) is None, f"Field `{field[0]}` in type `{xtype}` shadows field in embedded type `{xtype.embedded}`"

        # Unknown types will get an assert so we don't forget stuff
        else:
            assert False, f"Unknown type type {xtype.__class__}"

        return xtype

    def type_checking(self):
        from vstmt import StmtReturn

        if self.type_checked:
            return
        self.type_checked = True

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
            elif isinstance(ident, VBuiltinFunction):
                ident.type = self.resolve_type(ident.type)

            # If this is a type make sure it is resolved
            elif isinstance(ident, VType):
                self.identifiers[name] = self.resolve_type(ident)

            # For imported modules do type checking
            elif isinstance(ident, VModule):
                ident.type_checking()

        got_errors = False

        # Now the module level should be fine, we can do type checking on the
        # statement level
        for name in self.identifiers:
            ident = self.identifiers[name]
            if isinstance(ident, VFunction):
                # Do normal type checking
                if not ident.root_scope.type_check(self, ident.root_scope):
                    got_errors = True
                    continue

                # TODO: A bit more advanced return checks

                # Check return types
                if len(ident.type.return_types) > 0:
                    found = False
                    for stmt in ident.root_scope.code:
                        if isinstance(stmt, StmtReturn):
                            found = True
                            break
                    if not found:
                        ident.root_scope.reporter.reporter(ident.root_scope.line_end, 1, ident.root_scope.line_end + 1)('error', 'control reaches end of non-void function', func=ident.name)
                elif len(ident.root_scope.code) == 0 or not isinstance(ident.root_scope.code[-1], StmtReturn):
                    # Insert a return because this function has no return arguments and last item is not a return
                    ident.root_scope.code.append(StmtReturn([]))

        return got_errors

    def add_builtin_function(self, func):
        """
        :type func: VBuiltinFunction
        """
        func.type = self.add_type(func.type, lambda level, msg: print(f'<dynamic>: {level}: {msg}'))
        self.identifiers[func.name] = func


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


class VBuiltinFunction:

    def __init__(self, name, params, return_types):
        self.name = name

        self.type = VFunctionType()
        for p in params:
            self.type.add_param(False, VUnresolvedType(None, p))
        self.type.return_types = [VUnresolvedType(None, p) for p in return_types]


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
            return VVariable(self.param_names[index], self.type.param_types[index])
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
