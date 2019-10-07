from sly import Parser
from vlexer import VLexer
from typing import *

from vast import *
from vexpr import *
from vstmt import *


class VParser(Parser):
    tokens = VLexer.tokens

    def __init__(self):
        self.module_data = VModule()
        self.current_function = VFunction()
        self.current_scope = self.current_function.current_scope()

        # Add all builtin types
        self.module_data.add_type(VI8(False), 'i8')
        self.module_data.add_type(VI16(False), 'i16')
        self.module_data.add_type(VInt(False), 'int')
        self.module_data.add_type(VI64(False), 'i64')
        self.module_data.add_type(VI128(False), 'i128')
        self.module_data.add_type(VByte(False), 'byte')
        self.module_data.add_type(VU32(False), 'u16')
        self.module_data.add_type(VU32(False), 'u32')
        self.module_data.add_type(VU64(False), 'u64')
        self.module_data.add_type(VU128(False), 'u128')
        self.module_data.add_type(VBool(False), 'bool')

    precedence = (
        ('left', 'LOGICAL_OR'),
        ('left', 'LOGICAL_AND'),
        ('left', 'EQUALS', 'NOT_EQUALS', '>', 'GREATER_EQUALS', '<', 'LESS_EQUALS'),
        ('left', '+', '-', '|', '^'),
        ('left', '*', '/', '%', 'RIGHT_SHIFT', 'LEFT_SHIFT', '&')
    )

    ###################################################################################################
    # Module scope
    ###################################################################################################

    @_('module module_item')
    def module(self, p):
        return self.module_data

    @_('module_item')
    def module(self, p):
        return self.module_data

    @_('NEWLINE')
    def module_item(self, p):
        return self.module_data

    #
    # Function definition
    #

    @_('maybe_pub FN NAME "(" fn_args ")" fn_ret fn_block')
    def module_item(self, p):
        # set the properties of the function and add it
        self.current_function.pub = p.maybe_pub
        self.current_function.name = p.NAME

        # Resolve all types
        fn_args = p.fn_args  # type: List[Tuple[str, VType]]
        last_arg_type = None
        for i in reversed(range(len(fn_args))):
            fn_arg = fn_args[i]
            if fn_arg[1] is None:
                assert last_arg_type is not None
                fn_args[i] = (fn_arg[0], last_arg_type)
            else:
                last_arg_type = fn_arg[1]

        # Add all arguments to the function
        for fn_arg in fn_args:
            self.current_function.add_param(fn_arg[0], fn_arg[1])

        # Set the type correctly
        self.current_function.type = self.module_data.add_type(self.current_function.type)

        # Add the function
        self.module_data.add_function(p.NAME, self.current_function)

        # reset current function
        self.current_function = VFunction()
        self.current_scope = self.current_function.current_scope()

    @_('"{" stmt_list "}"')
    def fn_block(self, p):
        for stmt in p.stmt_list:
            self.current_scope.code.append(stmt)

    @_('"{" "}"')
    def fn_block(self, p):
        pass

    @_('fn_args "," fn_arg')
    def fn_args(self, p):
        if p.fn_arg is None:
            return p.fn_args
        return p.fn_args + [p.fn_arg]

    @_('fn_arg')
    def fn_args(self, p):
        if p.fn_arg is  None:
            return None
        return [p.fn_arg]

    @_('')
    def fn_args(self, p):
        return []

    @_('NAME type_decl')
    def fn_arg(self, p):
        return p.NAME, p.type_decl

    @_('NAME')
    def fn_arg(self, p):
        return p.NAME, None

    @_('type_decl')
    def fn_ret(self, p):
        self.current_function.add_return_type(p.type_decl)

    @_('"(" fn_ret_list ")"',
       '')
    def fn_ret(self, p):
        pass

    @_('fn_ret_list "," type_decl',
       'type_decl')
    def fn_ret_list(self, p):
        self.current_function.add_return_type(p.type_decl)

    #
    # Misc
    #

    @_('MODULE NAME')
    def module_item(self, p):
        self.module_data.set_module_name(p.NAME)

    @_('TYPE NAME type_decl')
    def module_item(self, p):
        self.module_data.add_type(p.type_decl, p.NAME)

    ###################################################################################################
    # Statement
    ###################################################################################################

    #
    # Statement list
    #

    @_('"{" stmt_list "}"')
    def stmt_block(self, p):
        self.current_scope = self.current_function.push_scope()
        for stmt in p.stmt_list:
            self.current_scope.code.append(stmt)
        self.current_scope = self.current_function.pop_scope()

    @_('"{" "}"')
    def stmt_block(self, p):
        pass

    @_('stmt_list stmt',
       'stmt')
    def stmt_list(self, p):
        try:
            if p.stmt is None:
                return p.stmt_list
            return p.stmt_list + [p.stmt]
        except:
            return []

    @_('stmt_list',
       '')
    def opt_stmt_list(self, p):
        try:
            return p.stmt_list
        except:
            return []

    #
    # Compound statement
    #

    @_('com_stmt "}"')
    def stmt(self, p):
        self.current_scope = self.current_function.pop_scope()

    @_('"{"')
    def com_stmt(self, p):
        self.current_scope = self.current_function.push_scope()

    @_('com_stmt stmt')
    def com_stmt(self, p):
        if p.stmt is not None:
            self.current_scope.code.append(p.stmt)

    #
    # if statement
    #

    @_('stmt_if')
    def stmt(self, p):
        return p.stmt_if

    @_('IF expr "{" opt_stmt_list "}" NEWLINE')
    def stmt_if(self, p):
        return StmtIf(p.expr, p.opt_stmt_list, None)

    @_('IF expr "{" opt_stmt_list "}" stmt_else')
    def stmt_if(self, p):
        return StmtIf(p.expr, p.opt_stmt_list, p.stmt_else)

    @_('ELSE "{" opt_stmt_list "}" NEWLINE')
    def stmt_else(self, p):
        return p.opt_stmt_list

    @_('ELSE stmt_if')
    def stmt_else(self, p):
        return [p.stmt_if]

    #
    # Variable declaration and assigning
    #

    @_('assign_name_list ASSIGN_DECLARE expr')
    def stmt(self, p):
        return StmtDeclare(p.assign_name_list, p.expr)

    @_('assign_name_list "," maybe_mut NAME')
    def assign_name_list(self, p):
        return p.assign_name_list + [(p.maybe_mut, p.NAME)]

    @_('maybe_mut NAME')
    def assign_name_list(self, p):
        return [(p.maybe_mut, p.NAME)]


    #
    # Misc statements
    #

    @_('CONTINUE')
    def stmt(self, p):
        return StmtContinue()

    @_('BREAK')
    def stmt(self, p):
        return StmtBreak()

    @_('RETURN expr_list NEWLINE')
    def stmt(self, p):
        return StmtReturn(p.expr_list)

    @_('ASSERT expr NEWLINE')
    def stmt(self, p):
        return StmtAssert(p.expr)

    @_('NEWLINE')
    def stmt(self, p):
        pass

    ###################################################################################################
    # Expressions
    ###################################################################################################

    #
    # Expr list
    #

    @_('expr_list "," expr')
    def expr_list(self, p):
        try:
            if p.expr is None:
                return p.expr_list
            return p.expr_list + [p.expr]
        except:
            return []

    @_('expr')
    def expr_list(self, p):
        if p.expr is None:
            return []
        return [p.expr]

    @_('')
    def expr_list(self, p):
        return []

    #
    # Binary Expressions
    #

    @_('expr "+" expr',
       'expr "-" expr',
       'expr "*" expr',
       'expr "/" expr',
       'expr "%" expr',
       'expr "&" expr',
       'expr "|" expr',
       'expr "^" expr',
       'expr LEFT_SHIFT expr',
       'expr RIGHT_SHIFT expr',

       'expr EQUALS expr',
       'expr NOT_EQUALS expr',
       'expr LESS_EQUALS expr',
       'expr GREATER_EQUALS expr',
       'expr "<" expr',
       'expr ">" expr'
       )
    def expr(self, p):
        return ExprBinary(p[1], p.expr0, p.expr1)

    #
    # Misc
    #

    @_('expr "(" expr_list ")"')
    def expr(self, p):
        return ExprFunctionCall(p.expr, p.expr_list)

    #
    # Literals
    #

    @_('NUMBER')
    def expr(self, p):
        return ExprIntegerLiteral(p.NUMBER)

    @_('NAME')
    def expr(self, p):
        return ExprIdentifierLiteral(p.NAME)

    @_('TRUE')
    def expr(self, p):
        return ExprBoolLiteral(True)

    @_('FALSE')
    def expr(self, p):
        return ExprBoolLiteral(False)

    ###################################################################################################
    # Helpers
    ###################################################################################################

    @_('maybe_mut NAME')
    def type_decl(self, p):
        # This will get resolved once we do type checking
        return VUnresolvedType(p.maybe_mut, p.NAME)

    @_('maybe_mut "[" "]" type_decl')
    def type_decl(self, p):
        return self.module_data.add_type(VArray(p.maybe_mut, p.type_decl))

    @_('maybe_mut "?" type_decl')
    def type_decl(self, p):
        return self.module_data.add_type(VOptional(p.maybe_mut, p.type_decl))

    @_('maybe_mut "&" type_decl')
    def type_decl(self, p):
        return self.module_data.add_type(VRef(p.maybe_mut, p.type_decl))

    @_('maybe_mut MAP "[" type_decl "]" type_decl')
    def type_decl(self, p):
        return self.module_data.add_type(VMap(p.maybe_mut, p.type_decl0, p.type_decl1))

    @_('')
    def maybe_mut(self, p):
        return False

    @_('MUT')
    def maybe_mut(self, p):
        return True

    @_('')
    def maybe_pub(self, p):
        return False

    @_('PUB')
    def maybe_pub(self, p):
        return True


