from vexpr import *
from typing import List
from vast import *


class StmtExpr(Stmt):

    def __init__(self, expr, report):
        """
        :type expr: Expr
        """
        super(StmtExpr, self).__init__(report)
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

    def __init__(self, expr, report):
        """
        :type expr: Expr
        """
        super(StmtAssert, self).__init__(report)
        self.expr = expr

    def type_check(self, module, scope):
        if not isinstance(self.expr.resolve_type(module, scope), VBool):
            raise TypeCheckError(self.expr.report, "assert requires a bool expression", scope.get_function().name)

    def __str__(self):
        return f'`assert {self.expr}`'


class StmtReturn(Stmt):

    def __init__(self, expr_list, report):
        """
        :type expr_list: List[Expr]
        """
        super(StmtReturn, self).__init__(report)
        self.exprs = expr_list

    def type_check(self, module, scope):
        func = scope.get_function()
        return_types = func.type.return_types  # type: List[Tuple[VType, bool]]
        assert len(return_types) == len(self.exprs)

        # TODO: Expending multiple return types

        for i in range(len(return_types)):
            to_type = return_types[i]

            expr = self.exprs[i]
            expr_type = expr.resolve_type(module, scope)

            default_assertion(expr_type, expr.report, scope.get_function().name)
            if to_type != expr_type:
                raise TypeCheckError(expr.report, f"return expected `{to_type}` for return at {i}, got `{expr_type}`", scope.get_function().name)

    def __str__(self):
        exprs = ', '.join(map(str, self.exprs))
        return f'`return {exprs}`'


class StmtDeclare(Stmt):

    def __init__(self, vars, expr, report):
        """
        :type vars: List[Tuple[bool, str]]
        :type expr: Expr
        """
        super(StmtDeclare, self).__init__(report)
        self.vars = vars
        self.expr = expr

    def type_check(self, module, scope):
        tlist = self.expr.resolve_type(module, scope)
        mutlist = self.expr.is_mut(module, scope)

        # This can handle the multiple return values from a function call
        if not isinstance(tlist, list):
            tlist = [tlist]
            mutlist = [mutlist]

        if len(self.vars) != len(tlist):
            raise TypeCheckError(self.report, f"Number of declarations does not match the number of return values (expected {len(tlist)}, got {len(self.vars)})", func=scope.get_function().name)

        for i in range(len(self.vars)):
            var = self.vars[i]
            var_type = tlist[i]
            from_mut = mutlist[i]
            default_assertion(var_type, self.report, scope.get_function().name)

            to_mut = var[0]
            name = var[1]

            # Override mutable if possible
            # 1. both are not mut
            # 2. both are mut
            # 3. assign mut to none mut
            if not from_mut and to_mut:
                raise TypeCheckError(self.expr.report, "Can not assign immutable type to a mutable variable", scope.get_function().name)

            scope.add_variable(name, to_mut, var_type)

    def __str__(self):
        s = ''
        for name in self.vars:
            s += f'{"mut " if name[0] else ""}{name[1]}'
        s += f' := {self.expr}'
        return s


class StmtContinue(Stmt):

    def __init__(self, report):
        super(StmtContinue, self).__init__(report)

    def type_check(self, module, scope):
        pass

    def __str__(self):
        return '`continue`'


class StmtBreak(Stmt):

    def __init__(self, report):
        super(StmtBreak, self).__init__(report)

    def type_check(self, module, scope):
        pass

    def __str__(self):
        return '`break`'


class StmtIf(Stmt):

    def __init__(self, expr, stmts_true, stmts_false, report):
        """
        :type expr: Expr
        :type stmts_true: List[Stmt]
        :type stmts_false: List[Stmt] or None
        """
        super(StmtIf, self).__init__(report)
        self.expr = expr
        self.stmts_true = stmts_true
        self.stmts_false = stmts_false

    def type_check(self, module, scope):
        t = self.expr.resolve_type(module, scope)
        if not isinstance(t, VBool):
            raise TypeCheckError(self.expr.report, f"if expected boolean, got `{t}`", scope.get_function().name)

        for stmt in self.stmts_true:
            stmt.type_check(module, scope)

        if self.stmts_false is not None:
            for stmt in self.stmts_false:
                stmt.type_check(module, scope)

    def __str__(self):
        return f'`if {self.expr}`'


class StmtAssign(Stmt):

    def __init__(self, dest, expr, report):
        """
        :type dest: Expr
        :type expr: Expr
        """
        super(StmtAssign, self).__init__(report)
        self.dest = dest
        self.expr = expr

    def type_check(self, module, scope):
        t0 = self.dest.resolve_type(module, scope)
        t1 = self.expr.resolve_type(module, scope)
        if t0 != t1:
            raise TypeCheckError(self.report, f"Can not assign `{t1}` to `{t0}`", scope.get_function().name)

        to_mut = self.dest.is_mut(module, scope)
        from_mut = self.expr.is_mut(module, scope)

        if not (to_mut and from_mut):
            raise TypeCheckError(self.expr.report, f"can not assign to immutable variable", scope.get_function().name)

    def __str__(self):
        return f'`{self.dest} = {self.expr}`'


class StmtFor(Stmt):

    def __init__(self, decl, condition, expr, stmts, report):
        """
        :type decl: StmtDeclare or None
        :type condition: Expr
        :type expe: Expr or StmtAssign
        :type stmts: List[Stmt]
        """
        super(StmtFor, self).__init__(report)
        self.decl = decl
        self.condition = condition
        self.expr = expr
        self.stmts = stmts

    def type_check(self, module, scope):
        # Check the declaration
        if self.decl is not None:
            self.decl.type_check(module, scope)

        # Check the condition
        t = self.condition.resolve_type(module, scope)
        if not isinstance(t, VBool):
            raise TypeCheckError(self.condition.report, f"for condition has to be bool, got `{t}`", scope.get_function().name)

        # Check the expr
        if isinstance(self.expr, Stmt):
            self.expr.type_check(module, scope)
        elif isinstance(self.expr, Expr):
            self.expr.resolve_type(module, scope)

        # Check all the statements
        for stmt in self.stmts:
            stmt.type_check(module, scope)

    def __str__(self):
        if self.decl is not None:
            return f'`for {self.decl}; {self.condition}; {self.expr}`'
        else:
            return f'`for ; {self.condition}; {self.expr}`'


class StmtForeach(Stmt):

    def __init__(self, index_name, item_name, expr, stmt_list, report):
        """
        :type index_name: str
        :type item_name: str
        :type expr: Expr
        :type stmt_list: List[Stmt]
        """
        super(StmtForeach, self).__init__(report)
        self.expr = expr
        self.index_name = index_name
        self.item_name = item_name
        self.stmts = stmt_list

    def type_check(self, module, scope):
        t = self.expr.resolve_type(module, scope)

        if isinstance(t, VArray):
            if self.index_name is not None:
                scope.add_variable(self.index_name, False, VInt)
            scope.add_variable(self.item_name, False, t.xtype)

        elif isinstance(t, VMap):
            if self.index_name is not None:
                scope.add_variable(self.index_name, False, t.key_type)
            scope.add_variable(self.item_name, False, t.value_type)

        else:
            raise TypeCheckError(self.expr.report, f"type `{t}` is not iterable", scope.get_function().name)

        # Check all the statements
        for stmt in self.stmts:
            stmt.type_check(module, scope)

    def __str__(self):
        if self.index_name is not None:
            return f'`for {self.index_name}, {self.item_name} in {self.expr}`'
        else:
            return f'`for {self.item_name} in {self.expr}`'
