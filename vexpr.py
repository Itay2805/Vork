from vtypes import *
from vast import *


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
        return VUntypedInteger(True)

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

        if isinstance(ident, VFunction):
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


