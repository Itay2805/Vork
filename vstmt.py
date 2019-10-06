from vexpr import Expr
from vtypes import *
from typing import List
from vast import *


class StmtExpr(Stmt):

    def __init__(self, expr):
        """
        :type expr: Expr
        """
        self.expr = expr

    def type_check(self, module, scope):
        """
        :type module: VModule
        :type scope: StmtCompound
        """
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


class StmtReturn(Stmt):

    def __init__(self, expr_list):
        """
        :type expr_list: List[Expr]
        """
        self.exprs = expr_list

    def type_check(self, module, scope):
        func = scope.get_function()
        return_types = func.type.return_types  # type: List[VType]
        assert len(return_types) == len(self.exprs)
        for i in range(len(return_types)):
            rtype = return_types[i]
            expr_type = self.exprs[i].resolve_type(module, scope)
            assert check_return_type(rtype, expr_type), f"return expected `{rtype}` for return at {i}, got `{expr_type}`"

    def __str__(self):
        exprs = ', '.join(map(str, self.exprs))
        return f'`return {exprs}`'
