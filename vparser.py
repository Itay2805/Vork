from lark import *
from vast import *
from vexpr import *
from vstmt import *


class ErrorReporter:

    def __init__(self, filename):
        self.filename = filename
        with open(filename) as f:
            self.code = f.readlines()

    def reporter_from_meta(self, tree):
        return self.reporter(tree.line, tree.column, tree.end_line, tree.end_column)

    def reporter(self, line, col, end_line=None, end_col=None):

        if end_line is None:
            end_line = line

        if end_col is None:
            end_col = col

        def report(level, msg, func=None):
            code_line = self.code[line - 1][:-1]

            # TODO: colorsss

            if func is not None:
                print(f'{self.filename}: In function `{func}`:')

            print(f'{self.filename}:{line}:{col}: {level}: {msg}')
            print(f'{code_line}')
            my_end_col = end_col - 1
            if end_line != line:
                my_end_col = len(code_line) - 1

            c = ''
            for i in range(col - 1):
                if code_line[i] == '\t':
                    c += '\t'
                else:
                    c += ' '
            print(c + '^' + '~' * (my_end_col - (col - 1) - 1))
            print()

        return report


@v_args(inline=True)
class VAstTransformer(Transformer):

    def __init__(self, reporter, workspace):
        super(VAstTransformer, self).__init__()
        self.workspace = workspace
        self.reporter = reporter
        self._temp_counter = 0

    def get_temp(self):
        self._temp_counter += 1
        return f'${self._temp_counter - 1}'

    def start(self, *args):
        # Find the module
        module = None  # type: VModule
        for arg in args:
            if isinstance(arg, tuple) and arg[0] == 'module' and isinstance(arg[1], VModule):
                # assert module is None, "Multiple module declarations is not allowed"
                if module is not None:
                    arg[2]('fatal', 'Multiple module declarations is not allowed')
                    return False
                module = arg[1]

        # TODO: Probably need to make sure this is the module we searched for

        # Default module is main
        if module is None:
            module = self.workspace.load_module('main')

        good = True

        to_check = []

        # Add all the args we got
        for arg in args:
            to_check.append(arg)

        # now we can load everything into the module scope
        while len(to_check) > 0:
            arg = to_check.pop()

            # Add function to module
            if isinstance(arg, VFunction):
                arg.type.module = module
                module.add_function(arg.name, arg, arg.report)

            # This is a type alias
            elif isinstance(arg, tuple) and isinstance(arg[0], str) and isinstance(arg[1], VType):
                name = arg[0]  # type: str
                xtype = arg[1]  # type: VType
                module.add_type(xtype, arg[2], name)

            # already handled the module decl
            elif isinstance(arg, tuple) and arg[0] == 'module' and isinstance(arg[1], VModule):
                pass

            elif isinstance(arg, tuple) and arg[0] == 'import' and isinstance(arg[1], list):
                mod = self.workspace.load_module('.'.join(arg[1]))
                if mod is None:
                    arg[2]('error', f'module `{".".join(arg[1])}` could not be imported')
                    good = False
                    continue
                module.identifiers[arg[1][-1]] = mod

            elif isinstance(arg, VStruct):
                arg.type.module = module
                arg.type = module.add_type(arg.type, arg.report, arg.name)

            elif isinstance(arg, VInteropFunction):
                # TODO: check duplicates
                module.identifiers[arg.interop_type][arg.name] = arg

            elif isinstance(arg, VConstant):
                if arg.name in module.identifiers:
                    arg.report('error', f'redefined `{arg.name}`')
                    good = False
                    continue
                module.identifiers[arg.name] = arg

            # List of stuff to add
            elif isinstance(arg, list):
                for a in arg:
                    to_check.append(a)

            elif arg is None:
                print("warning! got a None module item")

            # Unknown module item
            else:
                assert False, f"Unknown module item {arg}"

        return good

    ############################################################
    # Module scope
    ############################################################

    # Misc

    @v_args(meta=True)
    def module_decl(self, children, meta):
        return 'module', self.workspace.load_module(children[0]), self.reporter.reporter_from_meta(children[0])

    def type_alias_decl(self, name, xtype):
        return name, xtype

    @v_args(meta=True)
    def import_decl(self, children, meta):
        return 'import', list(map(str, children)), self.reporter.reporter_from_meta(meta)

    # Function declaration

    @v_args(meta=True)
    def interop_fn_decl(self, children, meta):

        if children[0] != 'C':
            self.reporter.reporter_from_meta(children[0])('error', f'Invalid interop `{children[0]}`')
            return None

        func = VInteropFunction(str(children[0]), str(children[1]))

        for param in children[2]:
            func.add_param(param[2], param[1])

        for rtype in children[3]:
            func.add_return_type(rtype)

        return func

    @v_args(meta=True)
    def fn_decl(self, children, meta):
        pub, name, params, return_types, stmts = children

        func = VFunction(self.reporter.reporter_from_meta(name))
        func.pub = pub
        func.name = str(name)

        for param in params:
            func.add_param(param[0], param[2], param[1])

        for rtype in return_types:
            func.add_return_type(rtype)

        func.root_scope = stmts
        func.root_scope.parent = func
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
        return list(return_types)

    # Struct declaration

    @v_args(tree=True)
    def struct_decl(self, tree):
        name, embedded, fields = tree.children

        # Process the fields and their access mods
        f = []
        ac = ACCESS_PRIVATE
        for field in fields:
            if isinstance(field, VStructField):
                field.access_mod = ac
                f.append(field)
            elif isinstance(field, str):
                ac = field

        return VStruct(str(name), VStructType(embedded, f), self.reporter.reporter_from_meta(name))

    def struct_fields(self, *fields):
        return list(fields)

    def struct_field(self, name, xtype):
        return VStructField(str(name), ACCESS_PRIVATE, xtype)

    def struct_access_mod(self, *mods):
        return ' '.join([str(m) for m in mods])

    def embedded_struct_field(self, *xtype):
        # TODO: return VUnresolvedType(xtype[0], xtype[1]) if len(xtype) > 0 else None
        return None

    # consts

    @v_args(meta=True)
    def const_decl(self, children, meta):
        return children

    @v_args(meta=True)
    def const_item(self, children, meta):
        return VConstant(str(children[0]), children[1], self.reporter.reporter_from_meta(children[0]))

    ############################################################
    # Statements
    ############################################################

    @v_args(meta=True)
    def stmt_return(self, children, meta):
        return StmtReturn(children, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_expr(self, children, meta):
        if children[0] is None or not isinstance(children[0], Expr):
            return None
        return StmtExpr(children[0], self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_assert(self, children, meta):
        # TODO: Maybe convert into a builtin function call
        return StmtAssert(children[0], self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_var_decl(self, children, meta):
        return StmtDeclare(children[0], children[1], self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def var_decl_vars(self, children, meta):
        return list(children)

    @v_args(meta=True)
    def var_decl(self, children, meta):
        return children[0], str(children[1])

    @v_args(meta=True)
    def stmt_if(self, children, meta):
        expr, stmt_list = children[:2]
        stmt_else = children[2:]
        return StmtIf(expr, stmt_list, stmt_else[0] if len(stmt_else) > 0 else None, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_else(self, children, meta):
        return children[0]

    @v_args(meta=True)
    def stmt_else_if(self, children, meta):
        return [children[0]]

    @v_args(meta=True)
    def stmt_assign(self, children, meta):
        dest, op, expr = children
        if len(op) == 1:
            return StmtAssign(dest, expr, self.reporter.reporter_from_meta(meta))
        else:
            return StmtAssign(dest, ExprBinary(op[:-1], dest, expr, self.reporter.reporter_from_meta(meta)), self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_forever(self, children, meta):
        # for -> for ; true; 0
        cond = ExprBoolLiteral(True, self.reporter.reporter_from_meta(meta))
        expr = ExprIntegerLiteral(0, self.reporter.reporter_from_meta(meta))

        return StmtFor(None, cond, expr, children[0][0], self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_foreach(self, children, meta):
        name, expr, stmts = children

        return StmtForeach(None, str(name), expr, stmts, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_foreach_indexed(self, children, meta):
        index, item, expr, stmts = children

        return StmtForeach(str(index), str(item), expr, stmts, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_for(self, children, meta):
        decl, condition, expr, stmt_list = children

        # Make the declared types be mut by default
        if isinstance(decl, StmtDeclare):
            for i in range(len(decl.vars)):
                decl.vars[i] = (True, decl.vars[i][1])

        return StmtFor(decl, condition, expr, stmt_list, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_break(self, children, meta):
        return StmtBreak(self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def stmt_continue(self, children, meta):
        return StmtContinue(self.reporter.reporter_from_meta(meta))

    ############################################################
    # Expressions
    ############################################################

    @v_args(meta=True)
    def expr_unary(self, children, meta):
        return ExprUnary(children[0], children[1], self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def expr_binary(self, children, meta):
        return ExprBinary(children[1], children[0], children[2], self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def expr_fn_call(self, children, meta):
        params = children[1:]
        parms = []
        for i in range(len(params) // 2):
            parms.append((params[i * 2], params[i * 2 + 1]))
        return ExprFunctionCall(children[0], parms, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def expr_member_access(self, children, meta):
        return ExprMemberAccess(children[0], str(children[1]), self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def expr_index(self, children, meta):
        return ExprIndex(children[0], children[1], self.reporter.reporter_from_meta(meta))

    ############################################################
    # Literals
    ############################################################

    @v_args(meta=True)
    def ident(self, children, meta):
        return ExprIdentifierLiteral(str(children[0]), self.reporter.reporter_from_meta(meta))

    def module_path_ident(self, *names):
        # TODO: Handle import stuff
        names = list(names)
        if len(names) == 1:
            return None, names[0]
        else:
            return self.workspace.load_module('.'.join(names[-1:])), names[-1]

    @v_args(meta=True)
    def number(self, children, meta):
        num = children[0]

        if num.startswith('0x'):
            num = int(num[2:], 16)
        elif num.startswith('0o'):
            num = int(num[2:], 8)
        elif num.startswith('0b'):
            num = int(num[2:], 2)
        else:
            num = int(num)

        return ExprIntegerLiteral(num, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def float(self, children, meta):
        return ExprFloatLiteral(float(children[0]), self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def const_true(self, children, meta):
        return ExprBoolLiteral(True, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def const_false(self, children, meta):
        return ExprBoolLiteral(False, self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def struct_literal(self, children, meta):
        ref, name = children[:2]
        # TODO: Need to extend this to support more than module local structs,
        # TODO: But also external module structs
        return ExprStructLiteral(ref, VUnresolvedType(name[0], name[1]), children[2:], self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def struct_literal_named(self, children, meta):
        ref, name = children[:2]
        elements = children[2:]
        return ExprStructLiteralNamed(ref, VUnresolvedType(name[0], name[1]), list(elements), self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def struct_literal_named_item(self, children, meta):
        return str(children[0]), children[1]

    @v_args(meta=True)
    def array_literal(self, children, meta):
        return ExprArrayLiteral(list(children), self.reporter.reporter_from_meta(meta))

    @v_args(meta=True)
    def array_literal_uninit(self, children, meta):
        return ExprArrayLiteralUninit(children[0], children[1], self.reporter.reporter_from_meta(meta))

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

    @v_args(meta=True)
    def stmt_list(self, children, meta):
        stmts_lst = []
        # TODO: From some reason sometimes stmt is inserted, will need to figure why
        for stmt in children:
            if isinstance(stmt, Stmt):
                stmts_lst.append(stmt)

        stmts = StmtCompound(None, self.reporter.reporter_from_meta(meta))
        stmts.code = stmts_lst
        stmts.line_start = meta.line
        stmts.line_end = meta.end_line
        stmts.reporter = self.reporter
        return stmts


VParser = Lark.open('v.lark', parser='earley', lexer='standard', propagate_positions=True)
