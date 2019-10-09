from vexpr import *
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

        # TODO: Expending multiple return types

        for i in range(len(return_types)):
            rtype = return_types[i]
            expr_type = self.exprs[i].resolve_type(module, scope)
            assert not isinstance(expr_type, list), "Expending function multiple results into a return is not supported yet"
            assert check_return_type(rtype, expr_type), f"return expected `{rtype}` for return at {i}, got `{expr_type}`"

    def __str__(self):
        exprs = ', '.join(map(str, self.exprs))
        return f'`return {exprs}`'


class StmtDeclare(Stmt):

    def __init__(self, names, expr):
        """
        :type names: List[Tuple[bool, str]]
        :type expr: Expr
        """
        self.names = names
        self.expr = expr

    def type_check(self, module, scope):
        tlist = self.expr.resolve_type(module, scope)

        # This can handle the multiple return values from a function call
        if not isinstance(tlist, list):
            tlist = [tlist]

        assert len(self.names) == len(tlist), f"Number of declarations does not match the number of return values (expected {len(tlist)}, got {len(self.names)})"

        for i in range(len(self.names)):
            name = self.names[i]
            t = tlist[i]
            default_assertion(t)

            mut_override = name[0]
            name = name[1]

            # Override mutable if possible
            assert not t.mut and not mut_override or not t.mut and mut_override, "Can not assign immutable type to a mutable variable"
            t = t.copy()
            t.mut = mut_override
            t = module.add_type(t)

            scope.add_variable(name, t)

    def __str__(self):
        s = ''
        for name in self.names:
            s += f'{"mut " if name[0] else ""}{name[1]}'
        s += f' := {self.expr}'
        return s


class StmtContinue(Stmt):

    def __init__(self):
        pass

    def type_check(self, module, scope):
        pass

    def __str__(self):
        return '`continue`'


class StmtBreak(Stmt):

    def __init__(self):
        pass

    def type_check(self, module, scope):
        pass

    def __str__(self):
        return '`break`'


class StmtIf(Stmt):

    def __init__(self, expr, stmt0, stmt1):
        """
        :type expr: Expr
        :type stmt0: List[Stmt]
        :type stmt1: List[Stmt] or None
        """
        self.expr = expr
        self.stmt0 = stmt0
        self.stmt1 = stmt1

    def type_check(self, module, scope):
        t = self.expr.resolve_type(module, scope)
        assert isinstance(t, VBool), f"if expected `{VBool}`, got `{t.__class__.__name__}`"

    def __str__(self):
        return f'`if {self.expr}`'
