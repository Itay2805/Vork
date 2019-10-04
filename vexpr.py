from vtypes import *


class Expr:

    def resolve_type(self):
        """
        :rtype: VType
        """
        raise NotImplementedError


class ExprIntegerLiteral(Expr):

    def __init__(self, num):
        """
        :type num: int
        """
        self.num = num

    def resolve_type(self):
        return VUntypedInteger(True)

    def __str__(self):
        return str(self.num)


class ExprBoolLiteral(Expr):

    def __init__(self, b):
        """
        :type b: bool
        """
        self.b = b

    def resolve_type(self):
        return VBool(False)

    def __str__(self):
        return str(self.b).lower()
