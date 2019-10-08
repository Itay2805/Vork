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
            if name in self.scope_stack[i]:
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

            for i in range(len(stmt.names)):
                self.call_stack[-1].set_variable(stmt.names[i][1], results[i])

        else:
            assert False, f"Unknown statement {stmt.__class__.__name__}"

    def _eval_function(self, func, params=None):
        """
        :param func: VFunction
        :param params: List[Any]
        """

        if isinstance(func, VFunction):
            self.call_stack.append(CallStackFrame(func, self.module))
            self.call_stack[-1].push_scope()

            # TODO: Check params
            for i in range(len(func.param_names)):
                self.call_stack[-1].set_variable(func.param_names[i], params[i])

            return self._eval_statement(func.root_scope)
        elif isinstance(func, VBuiltinFunction):
            if func.name != 'print':
                print(params)
            assert False, f"Unknown builtin function `{func.name}`"
        else:
            assert False, f"Unknown function `{func}`"

    def eval_function(self, name, params=None):
        return self._eval_function(self.module.get_identifier(name), params)
