from vast import *
from vtypes import default_value_for_type


def default_assertion(xtype):
    """
    Run these in most expressions

    These make sure the type is not void nor multiple return
    """
    assert not isinstance(xtype, list), "Expression can not take multiple return"
    assert not isinstance(xtype, VVoidType), "Expression can not take void return"


class ExprIntegerLiteral(Expr):

    def __init__(self, num):
        """
        :type num: int
        """
        self.num = num

    def resolve_type(self, module, scope):
        """
        :type module: VModule
        :type scope: StmtCompound
        :rtype: VType
        """

        # Always return a type of int, to override it use the casts
        return module.resolve_type(VInt(False))

    def __str__(self):
        return str(self.num)


class ExprBoolLiteral(Expr):

    def __init__(self, b):
        """
        :type b: bool
        """
        self.b = b

    def resolve_type(self, module, scope):
        return module.resolve_type(VBool(False))

    def __str__(self):
        return str(self.b).lower()


class ExprStructLiteral(Expr):

    def __init__(self, ref, xtype, fields):
        """
        :type ref: bool
        :type xtype: VStructType
        :type fields: List[Expr]
        """
        self.ref = ref
        self.xtype = xtype
        self.fields = fields

    def resolve_type(self, module, scope):
        # Don't forget to resolve it
        self.xtype = module.resolve_type(self.xtype)

        fields = self.fields

        # Check if there is an embedded type
        if self.xtype.embedded is not None and len(fields) > 0:
            if fields[0] is not None:
                t = fields[0].resolve_type(module, scope)
                assert check_return_type(self.xtype.embedded, t), f"Can not assign type `{t}` to embedded field (expected `{self.xtype.embedded}`)"
                fields = fields[1:]

        # check the rest of the types
        if len(fields) > 0:
            for field in self.xtype.fields:
                # None fields are default typed
                if fields[0] is not None:
                    t = fields[0].resolve_type(module, scope)
                    assert check_return_type(field[1], t), f"Can not assign type `{t}` to field `{self.xtype.name}.{field[0]}` (expected `{field[1]}`)"
                    fields = fields[1:]

                # The rest will be default typed
                if len(fields) == 0:
                    break

        # return the struct type
        if self.ref:
            # Remove the mutability of the type and pass it to the ref
            self.xtype = self.xtype.copy()
            self.xtype.mut = False
            self.xtype = module.add_type(self.xtype)
            return module.add_type(VRef(self.xtype.mut, self.xtype))

        return module.add_type(self.xtype)


class ExprIdentifierLiteral(Expr):

    def __init__(self, name):
        self.name = name

    def resolve_type(self, module, scope):
        ident = scope.get_identifier(self.name)
        if ident is None:
            ident = module.get_identifier(self.name)
        assert ident is not None, f"Unknown identifier `{self.name}`"

        if isinstance(ident, VFunction) or isinstance(ident, VBuiltinFunction):
            return ident.type

        elif isinstance(ident, VVariable):
            return ident.type

        elif isinstance(ident, VType):
            return ident

        else:
            assert False, f"Unexpected identifier type {ident.__class__}"

    def __str__(self):
        return self.name


class ExprBinary(Expr):

    POSSIBLE_TYPES = {
        '+': [VIntegerType],
        '-': [VIntegerType],
        '*': [VIntegerType],
        '/': [VIntegerType],
        '%': [VIntegerType],

        '&': [VIntegerType],
        '|': [VIntegerType],
        '^': [VIntegerType],

        '&&': [VBool],
        '||': [VBool],

        '>>': [VIntegerType],
        '<<': [VIntegerType],

        '==': ([VIntegerType, VBool], VBool(False)),
        '!=': ([VIntegerType, VBool], VBool(False)),
        '>=': ([VIntegerType, VBool], VBool(False)),
        '>':  ([VIntegerType, VBool], VBool(False)),
        '<=': ([VIntegerType, VBool], VBool(False)),
        '<':  ([VIntegerType, VBool], VBool(False)),
    }

    def __init__(self, op, expr0, expr1):
        """
        :type op: str
        :type expr0: Expr
        :type expr1: Expr
        """
        self.op = op
        self.expr0 = expr0
        self.expr1 = expr1

    def resolve_type(self, module, scope):
        t0 = self.expr0.resolve_type(module, scope)
        t1 = self.expr1.resolve_type(module, scope)

        default_assertion(t0)
        default_assertion(t1)

        # The types need to be the same
        # TODO: have this add casts or something
        assert check_return_type(t0, t1), f'Binary operators must have the same type on both sides (got `{t0}` and `{t1}`)'

        # Make sure we can use the operator on the given type
        good = False
        types = self.POSSIBLE_TYPES[self.op]

        # Type override
        got_type = t0
        if isinstance(types, tuple):
            got_type = types[1]
            types = types[0]

        # Check if fitting
        for xtype in types:
            if isinstance(t0, xtype):
                good = True
                break

        # TODO: Check for operator overloading functions

        assert good, f"Binary operator `{self.op}` can't be used on `{t0.__class__.__name__}`"

        return got_type

    def __str__(self):
        return f'{self.expr0} {self.op} {self.expr1}'


class ExprFunctionCall(Expr):
    """
    Will call the given function returning either a single value or multiple values
    """

    def __init__(self, func_expr, arguments):
        """
        :type func_expr: Expr
        :type arguments: List[Expr]
        """
        self.func_expr = func_expr
        self.arguments = arguments

    def resolve_type(self, module, scope):
        func = self.func_expr.resolve_type(module, scope)
        default_assertion(func)

        # Nomral functions
        if isinstance(func, VFunctionType):
            assert len(self.arguments) == len(func.param_types), f"expected {len(func.param_types)} arguments, got {len(self.arguments)}"
            for i in range(len(self.arguments)):
                t0 = self.arguments[i].resolve_type(module, scope)
                default_assertion(t0)
                t1 = func.param_types[i]
                assert check_return_type(t1, t0), f'function agument at `{i}` expected `{t1}`, got `{t0}`'

            # If returns one type, return 1 type
            if len(func.return_types) == 1:
                return func.return_types[0]

            # If does not return anything, return void type
            elif len(func.return_types) == 0:
                return VVoidType()

            # If has multiple types just return them all
            # TODO: make sure to handle list of types everywhere
            else:
                return func.return_types

        # int casts
        elif isinstance(func, VIntegerType):
            assert len(self.arguments) == 1, f"expected 1 argument for cast, got {len(self.arguments)}"
            t = self.arguments[0].resolve_type(module, scope)
            assert isinstance(t, VIntegerType), f"Integer cast requires an integer (got `{t}`)"
            return func

        else:
            assert False, f"the type `{func}` is not callable"

    def __str__(self):
        args = ', '.join(map(str, self.arguments))
        return f'{self.func_expr}({args})'


class ExprMemberAccess(Expr):
    """
    Will return the member of the given expression
    """

    def __init__(self, expr, member_name):
        """
        :type expr: Expr
        :type member_name: str
        """
        self.expr = expr
        self.member_name = member_name

    def resolve_type(self, module, scope):
        t = self.expr.resolve_type(module, scope)
        default_assertion(t)

        if isinstance(t, VStructType):
            newt = t.get_field(self.member_name)
            if newt is not None:
                return newt[1]

        elif isinstance(t, VArray):
            if self.member_name == 'len':
                return VInt(False)

        else:
            assert False, f"Type `{t}` does not have any members"

        assert False, f"Type `{t}` does not have member `{self.member_name}`"

    def __str__(self):
        return f'{self.expr}.{self.member_name}'


class ExprIndex(Expr):

    def __init__(self, src, at):
        """
        :type src: Expr
        :type at: Expr
        """
        self.src = src
        self.at = at

    def resolve_type(self, module, scope):
        t = self.src.resolve_type(module, scope)
        at_type = self.at.resolve_type(module, scope)
        default_assertion(t)
        default_assertion(at_type)

        if isinstance(t, VArray):
            assert isinstance(at_type, VIntegerType), f"array index must be an integer type (got {at_type})"
            return t.type

        elif isinstance(t, VMap):
            assert check_return_type(at_type, t.key), f"map of type {t} expected key {t.key}, got {at_type}"
            return t.value

        else:
            assert False, f"Index operator not supported for type {t}"

    def __str__(self):
        return f'{self.src}[{self.at}]'


class ExprArrayLiteral(Expr):
    """
    Return a new initialized array of the given expressions
    """

    def __init__(self, exprs):
        """
        :type exprs: List[Expr]
        """
        self.exprs = exprs

    def resolve_type(self, module, scope):
        xtype = None

        i = 0
        for expr in self.exprs:
            if xtype is None:
                xtype = expr.resolve_type(module, scope)
            else:
                xt = expr.resolve_type(module, scope)
                assert check_return_type(xtype, xt), f"Array item at index `{i}` does not match type (expected `{xtype}`, got `{xt}`)"
            i += 1

        default_assertion(xtype)

        return module.add_type(VArray(True, xtype))

    def __str__(self):
        return "[" + ','.join([str(expr) for expr in self.exprs]) + "]"


class ExprArrayLiteralUninit(Expr):
    """
    Returns a new un-initialized (default initialized) array of the given type
    with the given amount of starting elements
    """

    def __init__(self, length, xtype):
        """
        :type length: Expr
        :type xtype: VType
        """
        self.length = length
        self.xtype = xtype

    def resolve_type(self, module, scope):
        self.xtype = module.resolve_type(self.xtype)
        default_assertion(self.xtype)
        assert isinstance(self.length.resolve_type(module, scope), VIntegerType), "Length of array must be an integer"
        return module.add_type(VArray(True, self.xtype))

    def __str__(self):
        return f'[{self.length}]{self.xtype}'