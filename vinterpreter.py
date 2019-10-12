from vstmt import *
from vexpr import *
from typing import *


class CallStackFrame:

    def __init__(self, function, module):
        """
        :type function: VFunction
        :type module: VModule
        """
        self.module = module
        self.function = function
        self.scope_stack = []  # type: List[Dict[str, Any]]

    def push_scope(self):
        self.scope_stack.append({})

    def pop_scope(self):
        self.scope_stack.pop()

    def set_variable(self, name, value):
        self.scope_stack[-1][name] = value

    def get_variable(self, name):
        # Check in call stack level
        for i in reversed(range(len(self.scope_stack))):
            if name in self.scope_stack[i] and self.scope_stack[i][name] is not None:
                return self.scope_stack[i][name]

        # check in module level
        n = self.module.get_identifier(name)
        if n is not None:
            return n

        assert False, f"unknown variable (this should not happen...) ({name})"


class VInterpreter:

    def __init__(self, module):
        """
        :type module: VModule
        """
        self.module = module
        self.call_stack = []  # type: List[CallStackFrame]

    def _init_struct(self, expr, strct=None):
        """
        :type expr: ExprStructLiteral
        """
        fields = expr.fields

        if strct is None:
            strct = {}

        # TODO: Embedded type

        # Do none embedded types
        for field in expr.xtype.fields:
            if len(fields) > 0:
                strct[field[0]] = self._eval_expression(fields[0])
                fields = fields[1:]
            else:
                strct[field[0]] = self._eval_expression(default_value_for_type(field[1]))

        return strct

    def _eval_expression(self, expr):
        """
        :type expr: Expr
        """
        if isinstance(expr, ExprBoolLiteral):
            return expr.b

        elif isinstance(expr, ExprIntegerLiteral):
            return expr.num

        elif isinstance(expr, ExprIdentifierLiteral):
            return self.call_stack[-1].get_variable(expr.name)

        elif isinstance(expr, ExprBinary):
            return eval(f'{self._eval_expression(expr.expr0)} {expr.op} {self._eval_expression(expr.expr1)}')

        elif isinstance(expr, ExprFunctionCall):
            ret = self._eval_function(self._eval_expression(expr.func_expr), [self._eval_expression(e) for e in expr.arguments])
            if isinstance(ret, list):
                if len(ret) == 1:
                    return ret[0]
                else:
                    return ret
            else:
                return ret

        elif isinstance(expr, ExprStructLiteral):
            return self._init_struct(expr)

        elif isinstance(expr, ExprMemberAccess):
            return self._eval_expression(expr.expr)[expr.member_name]

        else:
            assert False, f"Unknown expression {expr}"

    def _eval_statement(self, stmt):
        """
        :type stmt: Stmt
        """
        if isinstance(stmt, StmtAssert):
            assert self._eval_expression(stmt.expr), f'V assert failed!'

        elif isinstance(stmt, StmtCompound):
            self.call_stack[-1].push_scope()
            for s in stmt.code:
                ret = self._eval_statement(s)
                if ret is not None:
                    return ret
            self.call_stack[-1].pop_scope()

        elif isinstance(stmt, StmtExpr):
            self._eval_expression(stmt.expr)

        elif isinstance(stmt, StmtReturn):
            exprs = []
            for e in stmt.exprs:
                exprs.append(self._eval_expression(e))
            self.call_stack.pop()
            return exprs

        elif isinstance(stmt, StmtIf):
            expr = self._eval_expression(stmt.expr)
            self.call_stack[-1].push_scope()

            # Eval the if
            if expr:
                for s in stmt.stmt0:
                    ret = self._eval_statement(s)
                    if ret is not None:
                        return ret

            # Eval the else
            else:
                if stmt.stmt1 is not None:
                    for s in stmt.stmt1:
                        ret = self._eval_statement(s)
                        if ret is not None:
                            return ret

            self.call_stack[-1].pop_scope()

        elif isinstance(stmt, StmtDeclare):
            expr = stmt.expr
            results = self._eval_expression(expr)

            if not isinstance(results, list):
                results = [results]

            for i in range(len(stmt.names)):
                self.call_stack[-1].set_variable(stmt.names[i][1], results[i])

        elif isinstance(stmt, StmtAssign):
            if isinstance(stmt.dest, ExprIdentifierLiteral):
                self.call_stack[-1].set_variable(stmt.dest.name, self._eval_expression(stmt.expr))

            elif isinstance(stmt.dest, ExprMemberAccess):
                self._eval_expression(stmt.dest.expr)[stmt.dest.member_name] = self._eval_expression(stmt.expr)

            else:
                assert False, f"Can not assign to expression `{stmt.dest}` ({stmt.dest.__class__})"

        else:
            assert False, f"Unknown statement {stmt.__class__.__name__}"

    def _eval_function(self, func, params=None):
        """
        :param func: VFunction
        :param params: List[Any]
        """

        if params is None:
            params = []

        if isinstance(func, VFunction):
            self.call_stack.append(CallStackFrame(func, self.module))
            self.call_stack[-1].push_scope()

            # TODO: Check params
            for i in range(len(func.param_names)):
                self.call_stack[-1].set_variable(func.param_names[i], params[i])

            return self._eval_statement(func.root_scope)
        elif isinstance(func, VBuiltinFunction):
            if func.name == 'print':
                print(params[0])
            else:
                assert False, f"Unknown builtin function `{func.name}`"
        else:
            assert False, f"Unknown function `{func}`"

    def eval_function(self, name, params=None):
        return self._eval_function(self.module.get_identifier(name), params)
