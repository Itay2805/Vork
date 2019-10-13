from vstmt import *
from vexpr import *
from typing import *


def assert_integer_cast(type, value):
    """
    :type type: VIntegerType
    :param value:
    :return:
    """
    if type.sign:
        max_val = (2 ** (type.bits / 2)) - 1
        min_val = (2 ** (type.bits / 2)) * -1
        assert min_val < value < max_val, f"can not cast from number `{value}` to `{type}` (min: {min_val}, max: {max_val})"
    else:
        max_val = (2 ** type.bits) - 1
        assert 0 < value < max_val, f"can not cast from number `{value}` to `{type}` (min: 0, max: {max_val})"


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
        self.should_break = False
        self.should_continue = False
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
            # TODO: Need a way to call this with bigger numbers
            assert_integer_cast(VInt, expr.num)
            return expr.num

        elif isinstance(expr, ExprIdentifierLiteral):
            return self.call_stack[-1].get_variable(expr.name)

        elif isinstance(expr, ExprBinary):
            return eval(f'{self._eval_expression(expr.expr0)} {expr.op} {self._eval_expression(expr.expr1)}')

        elif isinstance(expr, ExprUnary):
            return eval(f'{expr.op}{self._eval_expression(expr.expr)}')

        elif isinstance(expr, ExprFunctionCall):
            ret = self._eval_function(self._eval_expression(expr.func_expr), [self._eval_expression(e[1]) for e in expr.arguments])
            if isinstance(ret, tuple):
                if len(ret) == 1:
                    return ret[0]
                else:
                    return ret
            else:
                return ret

        elif isinstance(expr, ExprStructLiteral):
            return self._init_struct(expr)

        elif isinstance(expr, ExprMemberAccess):
            t = self._eval_expression(expr.expr)
            if isinstance(t, list):
                if expr.member_name == 'len':
                    return len(t)
            else:
                return [expr.member_name]

        elif isinstance(expr, ExprArrayLiteral):
            return [self._eval_expression(expr) for expr in expr.exprs]

        elif isinstance(expr, ExprArrayLiteralUninit):
            return [self._eval_expression(default_value_for_type(expr.xtype))] * self._eval_expression(expr.length)

        elif isinstance(expr, ExprIndex):
            return self._eval_expression(expr.src)[self._eval_expression(expr.at)]

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

                # If need to break or continue do that
                if self.should_continue or self.should_break:
                    break

            self.call_stack[-1].pop_scope()

        elif isinstance(stmt, StmtExpr):
            self._eval_expression(stmt.expr)

        elif isinstance(stmt, StmtReturn):
            exprs = []
            for e in stmt.exprs:
                exprs.append(self._eval_expression(e))
            self.call_stack.pop()
            return tuple(exprs)

        elif isinstance(stmt, StmtIf):
            expr = self._eval_expression(stmt.expr)
            self.call_stack[-1].push_scope()

            # Eval the if
            if expr:
                for s in stmt.stmts_true:
                    ret = self._eval_statement(s)
                    if ret is not None:
                        return ret

            # Eval the else
            else:
                if stmt.stmts_false is not None:
                    for s in stmt.stmts_false:
                        ret = self._eval_statement(s)
                        if ret is not None:
                            return ret

            self.call_stack[-1].pop_scope()

        elif isinstance(stmt, StmtDeclare):
            expr = stmt.expr
            results = self._eval_expression(expr)

            if not isinstance(results, tuple):
                results = [results]

            for i in range(len(results)):
                self.call_stack[-1].set_variable(stmt.vars[i][1], results[i])

        elif isinstance(stmt, StmtAssign):
            if isinstance(stmt.dest, ExprIdentifierLiteral):
                self.call_stack[-1].set_variable(stmt.dest.name, self._eval_expression(stmt.expr))

            elif isinstance(stmt.dest, ExprMemberAccess):
                self._eval_expression(stmt.dest.expr)[stmt.dest.member_name] = self._eval_expression(stmt.expr)

            elif isinstance(stmt.dest, ExprIndex):
                self._eval_expression(stmt.dest.src)[self._eval_expression(stmt.dest.at)] = self._eval_expression(stmt.expr)

            else:
                assert False, f"Can not assign to expression `{stmt.dest}` ({stmt.dest.__class__})"

        elif isinstance(stmt, StmtBreak):
            self.should_break = True

        elif isinstance(stmt, StmtContinue):
            self.should_continue = True

        elif isinstance(stmt, StmtFor):
            self.call_stack[-1].push_scope()
            should_run = True

            # Process the decl if needed
            if stmt.decl is not None:
                self._eval_statement(stmt.decl)

            # While the condition is true and we should run
            while should_run and self._eval_expression(stmt.condition):
                self.should_continue = False
                self.should_break = False

                for s in stmt.stmts:
                    ret = self._eval_statement(s)
                    if ret is not None:
                        return ret

                    # Break from running of statements
                    # and tell the loop to stop
                    if self.should_break:
                        should_run = False
                        break

                    # Break from the running of statements
                    # but continue running
                    elif self.should_continue:
                        break

                # Run the expression
                if not self.should_break:
                    if isinstance(stmt.expr, Stmt):
                        self._eval_statement(stmt.expr)
                    elif isinstance(stmt.expr, Expr):
                        self._eval_expression(stmt.expr)

            self.call_stack[-1].pop_scope()

        elif isinstance(stmt, StmtForeach):
            self.call_stack[-1].push_scope()
            should_run = True

            # TODO: Support maps

            # For the case of not indexed array
            if stmt.index_name is None:
                e = self._eval_expression(stmt.expr)
                for item in e:
                    self.call_stack[-1].set_variable(stmt.item_name, item)
                    for s in stmt.stmts:
                        ret = self._eval_statement(s)
                        if ret is not None:
                            return ret

                        # Break from running of statements
                        # and tell the loop to stop
                        if self.should_break:
                            should_run = False
                            break

                        # Break from the running of statements
                        # but continue running
                        elif self.should_continue:
                            break

                    if not should_run:
                        break

            # for the case of indexed array
            else:
                arr = self._eval_expression(stmt.expr)
                for index in range(len(arr)):
                    self.call_stack[-1].set_variable(stmt.item_name, arr[index])
                    self.call_stack[-1].set_variable(stmt.index_name, index)
                    for s in stmt.stmts:
                        ret = self._eval_statement(s)
                        if ret is not None:
                            return ret

                        # Break from running of statements
                        # and tell the loop to stop
                        if self.should_break:
                            should_run = False
                            break

                        # Break from the running of statements
                        # but continue running
                        elif self.should_continue:
                            break

                    if not should_run:
                        break

            self.call_stack[-1].pop_scope()


        else:
            assert False, f"Unknown statement {stmt.__class__.__name__}"

    def _eval_function(self, func, params=None):
        """
        :param func: VFunction
        :param params: List[Any]
        """

        if params is None:
            params = []

        # User defined function
        if isinstance(func, VFunction):
            self.call_stack.append(CallStackFrame(func, self.module))
            self.call_stack[-1].push_scope()

            # TODO: Check params
            for i in range(len(func.param_names)):
                self.call_stack[-1].set_variable(func.param_names[i], params[i])

            return self._eval_statement(func.root_scope)

        # Builtin function
        elif isinstance(func, VBuiltinFunction):
            if func.name == 'print':
                print(params[0])
            else:
                assert False, f"Unknown builtin function `{func.name}`"

        # Integer cast
        elif isinstance(func, VIntegerType):
            assert_integer_cast(func, params[0])
            return params[0]

        else:
            assert False, f"Unknown function `{func}`"

    def eval_function(self, name, params=None):
        return self._eval_function(self.module.get_identifier(name), params)
