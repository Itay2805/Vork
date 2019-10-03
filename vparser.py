from sly import Parser
from vlexer import VLexer


class VParser(Parser):
    tokens = VLexer.tokens

    debugfile = "test.out"

    precedence = (
        # TODO Assignment?
        # Logical OR
        ('left', 'LOGICAL_OR'),
        # Logical AND
        ('left', 'LOGICAL_AND'),
        # Bitwise OR
        ('left', '|'),
        # Bitwise XOR
        ('left', '^'),
        # Bitwise AND
        ('left', '&'),
        # Equality
        ('left', 'EQUALS', 'NOT_EQUALS'),
        # Relational
        ('left', '<', '>', 'LESS_EQUALS', 'GREATER_EQUALS'),
        # Shift
        ('left', 'RIGHT_SHIFT', 'LEFT_SHIFT'),
        # Additive
        ('left', '+', '-'),
        # Multiplicative
        ('left', '*', '/', '%'),
        # TODO: Unary
        # Postfix
        ('left', '(', '[', '.', 'IN'),
    )

    def __init__(self):
        self.env = {}

    ###################################################################################################
    # Module scope
    ###################################################################################################

    @_('module module_item')
    def module(self, p):
        if p.module_item is None:
            return p.module
        return p.module + [p.module_item]

    @_('module_item')
    def module(self, p):
        if p.module_item is None:
            return []
        return [p.module_item]

    @_('NEWLINE')
    def module_item(self, p):
        pass

    #
    # Function definition
    #

    @_('maybe_pub FN NAME "(" fn_args ")" fn_ret stmt_block')
    def module_item(self, p):
        return ('fn_decl', p.NAME, p.maybe_pub, p.fn_args, p.fn_ret, p.stmt_block)

    @_('')
    def fn_args(self, p):
        return []

    # TODO: Support for a, b int

    @_('fn_args "," NAME maybe_mut maybe_opt type_decl')
    def fn_args(self, p):
        return p.fn_args + [(p.NAME, p.maybe_mut, p.maybe_opt, p.type_decl)]

    @_('NAME maybe_mut maybe_opt type_decl')
    def fn_args(self, p):
        return [(p.NAME, p.maybe_mut, p.maybe_opt, p.type_decl)]

    @_('type_decl')
    def fn_ret(self, p):
        return [p.type_decl]

    @_('')
    def fn_ret(self, p):
        return []

    @_('"(" fn_ret_list ")"')
    def fn_ret(self, p):
        return p.fn_ret_list

    @_('fn_ret_list "," maybe_mut maybe_opt type_decl')
    def fn_ret_list(self, p):
        return p.fn_ret_list + [(p.maybe_mut, p.maybe_opt, p.type_decl)]

    @_('maybe_mut maybe_opt type_decl')
    def fn_ret_list(self, p):
        return [(p.maybe_mut, p.maybe_opt, p.type_decl)]

    #
    # Method definition
    #

    #
    # Struct definition
    #

    @_('STRUCT NAME "{" struct_items "}"')
    def module_item(self, p):
        return ('struct_decl', p.NAME, p.struct_items)

    @_('STRUCT NAME "{"  "}"')
    def module_item(self, p):
        return ('struct_decl', p.NAME, [])

    @_('struct_items struct_item')
    def struct_items(self, p):
        if p.struct_item is None:
            return p.struct_items
        return p.struct_items + [p.struct_item]

    @_('struct_item')
    def struct_items(self, p):
        if p.struct_item is None:
            return []
        return [p.struct_item]

    @_('NAME type_decl NEWLINE')
    def struct_item(self, p):
        return (p.NAME, p.type_decl)

    @_('type_decl NEWLINE')
    def struct_item(self, p):
        return ('', p.type_decl)

    @_('NEWLINE')
    def struct_item(self, p):
        return None

    #
    # Enum definition
    #

    @_('ENUM NAME "{" enum_items "}"')
    def module_item(self, p):
        return ('enum_decl', p.NAME, p.enum_items)

    @_('ENUM NAME "{" "}"')
    def module_item(self, p):
        return ('enum_decl', [])

    @_('enum_items enum_item')
    def enum_items(self, p):
        if p.enum_item is None:
            return p.enum_items
        return p.enum_items + [p.enum_item]

    @_('enum_item')
    def enum_items(self, p):
        if p.enum_item is None:
            return []
        return [p.enum_item]

    @_('NAME')
    def enum_item(self, p):
        return p.NAME

    @_('NEWLINE')
    def enum_item(self, p):
        return None

    #
    # Misc
    #

    @_('MODULE NAME')
    def module_item(self, p):
        return ('module', p.NAME)

    @_('IMPORT NAME')
    def module_item(self, p):
        return ('import', p.NAME)

    ###################################################################################################
    # Statement
    ###################################################################################################

    #
    # Statement list
    #

    @_('"{" stmt_list "}"')
    def stmt_block(self, p):
        return p.stmt_list

    @_('"{" "}"')
    def stmt_block(self, p):
        return []

    @_('stmt_list stmt')
    def stmt_list(self, p):
        if p.stmt is None:
            return p.stmt_list
        return p.stmt_list + [p.stmt]

    @_('stmt')
    def stmt_list(self, p):
        if p.stmt is None:
            return []
        return [p.stmt]

    @_('"{"')
    def com_stmt(self, p):
        return []

    @_('com_stmt stmt')
    def com_stmt(self, p):
        if p.stmt is None:
            return p.com_stmt
        return p.com_stmt + [p.stmt]

    @_('com_stmt "}"')
    def stmt(self, p):
        return p.com_stmt

    #
    # Return stmt
    #

    @_('RETURN return_list_item NEWLINE')
    def stmt(self, p):
        return ('return', p.return_list_item)

    @_('')
    def return_list_item(self, p):
        return []

    @_('return_list_item "," expr')
    def return_list_item(self, p):
        return p.return_list_item + [p.expr]

    @_('expr')
    def return_list_item(self, p):
        return [p.expr]

    #
    # var declaration
    #

    @_('MUT NAME ASSIGN_DECLARE expr NEWLINE')
    def stmt(self, p):
        return ('var_decl', True, p.NAME, p.expr)

    @_('NAME ASSIGN_DECLARE expr NEWLINE')
    def stmt(self, p):
        return ('var_decl', False, p.NAME, p.expr)

    #
    # Variable declaration
    #

    @_('expr NEWLINE')
    def stmt(self, p):
        return p.expr

    #
    # If statement
    #

    @_('IF expr stmt_block NEWLINE')
    def stmt(self, p):
        return ('if', p.expr, p.stmt_block, None)

    @_('IF expr stmt_block ELSE stmt_block NEWLINE')
    def stmt(self, p):
        return ('if', p.expr, p.stmt_block0, p.stmt_block1)

    # TODO: else if...

    #
    # For statement
    #

    @_('FOR stmt_block NEWLINE')
    def stmt(self, p):
        return ('for_ever', p.stmt_block)

    @_('FOR NAME IN expr stmt_block NEWLINE')
    def stmt(self, p):
        return ('for_each', None, p.NAME, p.expr, p.stmt_block)

    @_('FOR NAME "," NAME IN expr stmt_block NEWLINE')
    def stmt(self, p):
        return ('for_each', p.NAME0, p.NAME1, p.expr, p.stmt_block)

    # TODO: a bit hacky, so we can have both the assign statement and expressions in the last place
    # TODO: also for now we only allow a declaration inside the first thing
    # TODO: also also, none of them can be empty

    @_('FOR NAME ASSIGN_DECLARE expr ";" expr ";" assign_stmt stmt_block NEWLINE')
    def stmt(self, p):
        return ('for', (p.NAME, p.expr0), p.expr1, p.assign_stmt, p.stmt_block)

    @_('FOR NAME ASSIGN_DECLARE expr ";" expr ";" expr stmt_block NEWLINE')
    def stmt(self, p):
        return ('for', (p.NAME, p.expr0), p.expr1, p.expr2, p.stmt_block)

    #
    # Assign statement
    #

    @_('assign_stmt NEWLINE')
    def stmt(self, p):
        return p.assign_stmt

    @_('expr ASSIGN_ADD expr',
       'expr ASSIGN_SUB expr',
       'expr ASSIGN_MUL expr',
       'expr ASSIGN_DIV expr',
       'expr ASSIGN_MOD expr',
       'expr ASSIGN_AND expr',
       'expr ASSIGN_OR expr',
       'expr ASSIGN_XOR expr',
       'expr ASSIGN_LEFT_SHIFT expr',
       'expr ASSIGN_RIGHT_SHIFT expr',
       )
    def assign_stmt(self, p):
        expr_list = {
            '+=': 'add',
            '-=': 'sub',
            '*=': 'mul',
            '/=': 'div',
            '%=': 'mod',
            '&=': 'bitwise_and',
            '|=': 'bitwise_or',
            '^=': 'bitwise_xor',
            '<<=': 'left_shift',
            '>>=': 'right_shift',
        }
        # This makes sure we have no side effects
        return [
            ('temp_decl', 0, p.expr0),
            ('assign',
             ('temp', 0),
             (expr_list[p[1]],
              ('temp', 0),
              p.expr1
              )
             )
        ]

    @_('expr "=" expr')
    def assign_stmt(self, p):
        return ('assign', p.expr0, p.expr1)

    #
    # Misc
    #

    @_('DEFER expr NEWLINE')
    def stmt(self, p):
        return ('defer', p.expr)

    @_('BREAK NEWLINE')
    def stmt(self, p):
        return ('break')

    @_('CONTINUE NEWLINE')
    def stmt(self, p):
        return ('continue')

    @_('ASSERT expr NEWLINE')
    def stmt(self, p):
        return ('assert', p.expr)

    @_('NEWLINE')
    def stmt(self, p):
        return None

    ###################################################################################################
    # Expressions
    ###################################################################################################

    #
    # Expr list
    #

    @_('expr_list "," expr')
    def expr_list(self, p):
        return p.expr_list + [p.expr]

    @_('expr')
    def expr_list(self, p):
        return [p.expr]

    @_('')
    def expr_list(self, p):
        return []

    #
    # Binary expressions
    #

    @_('expr ">" expr',
       'expr "<" expr',
       'expr NOT_EQUALS expr',
       'expr EQUALS expr',
       'expr LESS_EQUALS expr',
       'expr GREATER_EQUALS expr',
       'expr "+" expr',
       'expr "-" expr',
       'expr "*" expr',
       'expr "/" expr',
       'expr "%" expr',
       'expr "&" expr',
       'expr "|" expr',
       'expr "^" expr',
       'expr LOGICAL_AND expr',
       'expr LOGICAL_OR expr',
       'expr LEFT_SHIFT expr',
       'expr RIGHT_SHIFT expr')
    def expr(self, p):
        expr_map = {
            '>': 'greater',
            '<': 'less',
            '!=': 'not_equals',
            '==': 'equals',
            '<=': 'less_equals',
            '>=': 'greater_equals',
            '+': 'add',
            '-': 'sub',
            '*': 'mul',
            '/': 'div',
            '%': 'mod',
            '&': 'bitwise_and',
            '|': 'bitwise_or',
            '^': 'bitwise_xor',
            '||': 'logical_or',
            '&&': 'logical_and',
            '<<': 'left_shift',
            '>>': 'right_shift',
        }
        return (expr_map[p[1]], p.expr0, p.expr1)

    #
    # Misc
    #

    @_('expr "[" expr "]"')
    def expr(self, p):
        return ('access_index', p.expr0, p.expr1)

    @_('expr "(" fn_param_list ")"')
    def expr(self, p):
        return ('fn_call', p.expr, p.fn_param_list)

    @_('fn_param_list "," maybe_mut maybe_opt expr')
    def fn_param_list(self, p):
        return p.fn_param_list + [(p.maybe_mut, p.maybe_opt, p.expr)]

    @_('maybe_mut maybe_opt expr')
    def fn_param_list(self, p):
        return [(p.maybe_mut, p.maybe_opt, p.expr)]

    @_('')
    def fn_param_list(self, p):
        return []

    @_('expr "." expr')
    def expr(self, p):
        return ('member_access', p.expr0, p.expr1)

    @_('expr IN expr')
    def expr(self, p):
        return ('in', p.expr0, p.expr1)

    # WTF?
    # @_('expr OR stmt_block')
    # def expr(self, p):
    #     return ('or', p.expr, p.stmt_block)

    #:
    # Literal expressions
    #

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('"[" expr_list "]"')
    def expr(self, p):
        return ('arr', p.expr_list)

    @_('NAME')
    def expr(self, p):
        return ('var', p.NAME)

    @_('NUMBER')
    def expr(self, p):
        return ('num', p.NUMBER)

    @_('STRING')
    def expr(self, p):
        return ('str', p.STRING)

    @_('CHAR')
    def expr(self, p):
        return ('chr', p.CHAR)

    ###################################################################################################
    # Helpers
    ###################################################################################################

    @_('NAME')
    def type_decl(self, p):
        return ('base_type', p.NAME)

    @_('"[" "]" type_decl')
    def type_decl(self, p):
        return ('array_type', p.type_decl)

    @_('"&" type_decl')
    def type_decl(self, p):
        return ('ref_type', p.type_decl)

    @_('MAP "[" type_decl "]" type_decl')
    def type_decl(self, p):
        return ('map_type', p.type_decl0, p.type_decl1)

    # TODO: Can we have an optional optional?
    @_('')
    def maybe_opt(self, p):
        return False

    @_('"?"')
    def maybe_opt(self, p):
        return True

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