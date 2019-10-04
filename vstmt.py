from vexpr import Expr


class Stmt:
    pass


class StmtExpr(Stmt):

    def __init__(self, expr):
        """
        :type expr: Expr
        """
        self.expr = expr

    def __str__(self):
        return f"`{self.expr}`"


class StmtAssert(Stmt):

    def __init__(self, expr):
        """
        :type expr: Expr
        """
        self.expr = expr

    def __str__(self):
        return f'`assert {self.expr}`'
