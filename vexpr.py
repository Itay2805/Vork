from vast import *


def default_assertion(xtype):
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

        # quick way to get the number of needed bits
        # we exclude the last bit in each type because the literal is signed
        # TODO: maybe want to allow for unsigned literals as well
        # TODO: maybe we want literals by default to be an int always?
        bits = len(bin(self.num)[2:])
        if bits < 8:
            return VI8(False)
        elif bits < 16:
            return VI16(False)
        elif bits < 32:
            return VI16(False)
        elif bits < 64:
            return VInt(False)
        elif bits < 128:
            return VI128(False)

    def __str__(self):
        return str(self.num)


class ExprBoolLiteral(Expr):

    def __init__(self, b):
        """
        :type b: bool
        """
        self.b = b

    def resolve_type(self, module, scope):
        return VBool(False)

    def __str__(self):
        return str(self.b).lower()


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

    def __init__(self, func_expr, arguments):
        """
        :type func_expr: Expr
        :type arguments: List[Expr]
        """
        self.func_expr = func_expr
        self.arguments = arguments

    def resolve_type(self, module, scope):
        func = self.func_expr.resolve_type(module, scope)
        assert isinstance(func, VFunctionType), f"function call expected function, got `{func}`"
        default_assertion(func)

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

    def __str__(self):
        args = ', '.join(map(str, self.arguments))
        return f'{self.func_expr}({args})'

