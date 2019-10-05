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
        # TODO: operator overloading
        t0 = self.expr0.resolve_type(module, scope)
        t1 = self.expr1.resolve_type(module, scope)

        # The types need to be the same
        # TODO: Might wanna ignore mut
        assert are_compatible_types(t0, t1), f'Binary operators must have the same type on both sides (got `{t0}` and `{t1}`)'

        # Make sure we can use the operator on the given type
        good = False
        types = self.POSSIBLE_TYPES[self.op]
        for type in types:
            if isinstance(t0, type):
                good = True
                break
        assert good, f"Binary operator `{self.op}` can't be used on `{t0.__class__.__name__}`"

        return t0

    def __str__(self):
        return f'{self.expr0} {self.op} {self.expr1}'


