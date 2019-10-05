from vexpr import Expr
from vtypes import *


class Stmt:

    def type_check(self, module, scope):
        raise NotImplementedError


class StmtExpr(Stmt):

    def __init__(self, expr):
        """
        :type expr: Expr
        """
        self.expr = expr

    def type_check(self, module, scope):
        self.expr.resolve_type(module, scope)

    def __str__(self):
        return f"`{self.expr}`"


class StmtAssert(Stmt):

    def __init__(self, expr):
        """
        :type expr: Expr
        """
        self.expr = expr

    def type_check(self, module, scope):
        assert isinstance(self.expr.resolve_type(module, scope), VBool), "assert requires a bool expression"

    def __str__(self):
        return f'`assert {self.expr}`'
