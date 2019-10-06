from vast import *
from vstmt import *
from vexpr import *
from typing import *

class CallStackFrame:

    def __init__(self, function):
        self.function = function
        self.scope_stack = []  # type: List[Dict[str, Any]]

    def push_scope(self):
        self.scope_stack.append({})

    def pop_scope(self):
        self.scope_stack.pop()

    def set_variable(self, name, value):
        self.scope_stack[-1][name] = value

    def get_variable(self, name):
        for i in reversed(range(len(self.scope_stack))):
            if name in self.scope_stack[i]:
                return self.scope_stack[i][name]
        assert False, "unknown variable (this should not happen...)"


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
            self.call_stack[-1].set_variable(stmt.name, self._eval_expression(stmt.expr))
        else:
            assert False, f"Unknown statement {stmt.__class__.__name__}"

    def run_function(self, name, params=None):
        func = self.module.identifiers[name]
        assert isinstance(func, VFunction);
        self.call_stack.append(CallStackFrame(func))
        self.call_stack[-1].push_scope()

        # TODO: Check params
        for i in range(len(func.param_names)):
            self.call_stack[-1].set_variable(func.param_names[i], params[i])

        return self._eval_statement(func.root_scope)


