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
                arg.type.module = module
                module.add_function(arg.name, arg)

            # This is a type alias
            elif isinstance(arg, tuple) and isinstance(arg[0], str) and isinstance(arg[1], VType):
                name = arg[0]  # type: str
                xtype = arg[1]  # type: VType
                module.add_type(xtype, name)

            # already handled the module decl
            elif isinstance(arg, tuple) and arg[0] == 'module' and isinstance(arg[1], VModule):
                pass

            elif isinstance(arg, VStruct):
                arg.type.module = module
                arg.type = module.add_type(arg.type)

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
            func.add_param(param[0], param[2], param[1])

        for rtype in return_types:
            func.add_return_type(rtype[0], rtype[1])

        func.root_scope.code = stmts
        func.root_scope.fix_children()
        return func

    def fn_params(self, *params):
        params = list(params)
        last_type = None
        for i in reversed(range(len(params))):
            param = params[i]
            if param[1] is None:
                assert last_type is not None
                params[i] = (param[0], last_type, param[2])
            else:
                last_type = param[1]
        return params

    def fn_param(self, *args):
        if len(args) == 1:
            return str(args[0]), None, False
        else:
            return str(args[0]), args[2], args[1]

    def fn_return(self, *return_types):
        rets = []
        for i in range(len(return_types) // 2):
            rets.append((return_types[i], return_types[i + 1]))
        return rets

    # Struct declaration

    def struct_decl(self, name, embedded, fields):

        # Process the fields and their access mods
        f = []
        ac = ACCESS_PRIVATE
        for field in fields:
            if isinstance(field, VStructField):
                field.access_mod = ac
                f.append(field)
            elif isinstance(field, str):
                ac = field

        return VStruct(str(name), VStructType(embedded, f))

    def struct_fields(self, *fields):
        return list(fields)

    def struct_field(self, name, xtype):
        return str(name), xtype

    def embedded_struct_field(self, *xtype):
        # TODO: return VUnresolvedType(xtype[0], xtype[1]) if len(xtype) > 0 else None
        return None

    ############################################################
    # Statements
    ############################################################

    def stmt_return(self, *exprs):
        return StmtReturn(list(exprs))

    def stmt_expr(self, expr):
        if expr is None or not isinstance(expr, Expr):
            return None
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

    def stmt_assign(self, dest, expr):
        return StmtAssign(dest, expr)

    def stmt_forever(self, stmt_list):
        # for -> for ; true; 0
        return StmtFor(None, ExprBoolLiteral(True), ExprIntegerLiteral(0), stmt_list)

    def stmt_foreach(self, name, expr, stmts):
        return StmtForeach(None, str(name), expr, stmts)

    def stmt_foreach_indexed(self, index, item, expr, stmts):
        return StmtForeach(str(index), str(item), expr, stmts)

    def stmt_for(self, decl, condition, expr, stmt_list):
        # Return that scope
        return StmtFor(decl, condition, expr, stmt_list)

    def stmt_break(self):
        return StmtBreak()

    def stmt_continue(self):
        return StmtContinue()

    ############################################################
    # Expressions
    ############################################################

    def expr_binary(self, expr0, op, expr1):
        return ExprBinary(op, expr0, expr1)

    def expr_fn_call(self, fn_expr, *params):
        parms = []
        for i in range(len(params) // 2):
            parms.append((params[i], params[i + 1]))
        return ExprFunctionCall(fn_expr, parms)

    def expr_member_access(self, expr, member_name):
        return ExprMemberAccess(expr, str(member_name))

    def expr_index(self, src, at):
        return ExprIndex(src, at)

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

    def struct_literal(self, ref, name, *exprs):
        # TODO: Need to extend this to support more than module local structs,
        # TODO: But also external module structs
        return ExprStructLiteral(ref, VUnresolvedType(None, str(name)), list(exprs))

    def array_literal(self, *exprs):
        return ExprArrayLiteral(list(exprs))

    def array_literal_uninit(self, size, xtype):
        return ExprArrayLiteralUninit(size, xtype)

    ############################################################
    # Type declarations
    ############################################################

    def type_ident(self, xtype):
        return VUnresolvedType(None, xtype)

    def type_array(self, xtype):
        return VArray(xtype)

    def type_map(self, keyt, valuet):
        return VMap(keyt, valuet)

    def type_ref(self, xtype):
        return VRef(xtype)

    def type_opt(self, xtype):
        return VOptional(xtype)

    ############################################################
    # Helpers
    ############################################################

    def maybe_mut(self, *args):
        return len(args) != 0

    def maybe_pub(self, *args):
        return len(args) != 0

    def maybe_ref(self, *args):
        return len(args) != 0

    def maybe_var_decl(self, *args):
        if len(args) != 0:
            return args[0]
        else:
            return None

    def stmt_list(self, *stmts):
        stmts_lst = []
        # TODO: From some reason sometimes stmt is inserted, will need to figure why
        for stmt in stmts:
            if isinstance(stmt, Stmt):
                stmts_lst.append(stmt)
        return stmts_lst


VParser = Lark.open('v.lark')
