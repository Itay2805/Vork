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
