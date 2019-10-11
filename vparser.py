from lark import *
from vast import *
from vexpr import *
from vstmt import *


@v_args(inline=True)
class VAstTransformer(Transformer):

    def __init__(self, workspace):
        super(VAstTransformer, self).__init__()
        self.workspace = workspace

    def start(self, *args):
        # Find the module
        module = None  # type: Optional[VModule]
        for arg in args:
            if isinstance(arg, tuple) and arg[0] == 'module' and isinstance(arg[1], VModule):
                assert module is None, "Multiple module declarations is not allowed"
                module = arg[1]

        # Default module is main
        if module is None:
            module = self.workspace.load_module('main')

        # now we can load everything into the module scope
        for arg in args:
            # Add function to module
            if isinstance(arg, VFunction):
                arg.module = module
                module.add_function(arg.name, arg)

            # This is a type alias
            elif isinstance(arg, tuple) and isinstance(arg[0], str) and isinstance(arg[1], VType):
                name = arg[0]  # type: str
                xtype = arg[1]  # type: VType
                module.add_type(xtype, name)

            # already handled the module decl
            elif isinstance(arg, tuple) and arg[0] == 'module' and isinstance(arg[1], VModule):
                pass

            # Unknown module item
            else:
                assert False, f"Unknown module item {arg}"

        return module

    ############################################################
    # Module scope
    ############################################################

    # Misc

    def module_decl(self, name):
        return 'module', self.workspace.load_module(name)

    def type_alias_decl(self, name, xtype):
        return name, xtype

    # Function declaration

    def fn_decl(self, pub, name, params, return_types, stmts):
        func = VFunction()
        func.pub = pub
        func.name = str(name)
        for param in params:
            func.add_param(param[0], param[1])
        for rtype in return_types:
            func.add_return_type(rtype)
        func.root_scope.code = stmts
        return func

    def fn_params(self, *params):
        params = list(params)
        last_type = None
        for i in reversed(range(len(params))):
            if params[i][1] is None:
                assert last_type is not None
                params[i] = (params[i][0], last_type)
            else:
                last_type = params[i][1]
        return params

    def fn_param(self, *args):
        if len(args) == 1:
            return str(args[0]), None
        else:
            return str(args[0]), args[1]

    def fn_return(self, *return_types):
        return list(return_types)

    # Struct declaration

    def struct_decl(self, name, embedded, fields):
        return name, VStructType(False, embedded, fields)

    def struct_fields(self, *fields):
        return list(fields)

    def struct_field(self, name, xtype):
        return name, xtype

    def embedded_struct_field(self, *xtype):
        return xtype[0] if len(xtype) > 0 else None

    ############################################################
    # Statements
    ############################################################

    def stmt_return(self, *exprs):
        return StmtReturn(list(exprs))

    def stmt_expr(self, expr):
        return StmtExpr(expr)

    def stmt_assert(self, expr):
        # TODO: Maybe convert into a builtin function call
        return StmtAssert(expr)

    def stmt_var_decl(self, names, expr):
        return StmtDeclare(names, expr)

    def var_decl_names(self, *args):
        return list(args)

    def var_decl(self, mut, name):
        return mut, str(name)

    def stmt_if(self, expr, stmt_list, *stmt_else):
        return StmtIf(expr, stmt_list, stmt_else[0] if len(stmt_else) > 0 else None)

    def stmt_else(self, stmt_list):
        return stmt_list

    def stmt_else_if(self, stmt_if):
        return [stmt_if]

    ############################################################
    # Expressions
    ############################################################

    def expr_binary(self, expr0, op, expr1):
        return ExprBinary(op, expr0, expr1)

    def expr_fn_call(self, fn_name, *params):
        return ExprFunctionCall(fn_name, list(params))

    ############################################################
    # Literals
    ############################################################

    def ident(self, name):
        return ExprIdentifierLiteral(str(name))

    def number(self, num):
        return ExprIntegerLiteral(int(num))

    def const_true(self):
        return ExprBoolLiteral(True)

    def const_false(self):
        return ExprBoolLiteral(False)

    ############################################################
    # Type declarations
    ############################################################

    def type_ident(self, mut, xtype):
        return VUnresolvedType(mut, xtype)

    ############################################################
    # Helpers
    ############################################################

    def maybe_mut(self, *args):
        return len(args) != 0

    def maybe_pub(self, *args):
        return len(args) != 0

    def stmt_list(self, *stmts):
        stmts_lst = []
        # TODO: From some reason sometimes stmt is inserted, will need to figure why
        for stmt in stmts:
            if isinstance(stmt, Stmt):
                stmts_lst.append(stmt)
        return stmts_lst


VParser = Lark.open('v.lark')
