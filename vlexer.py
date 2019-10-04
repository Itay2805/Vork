from sly import Lexer


class VLexer(Lexer):
    tokens = {
        BREAK, CONST, CONTINUE, DEFER, ELSE, ENUM, FN,
        FOR, GO, GOTO, IF, IMPORT, IN, INTERFACE, MATCH,
        MODULE, MUT, OR, PUB, RETURN, STRUCT, TYPE, MAP,
        ASSERT, TRUE, FALSE,

        LEFT_SHIFT, RIGHT_SHIFT, EQUALS, NOT_EQUALS,
        LESS_EQUALS, GREATER_EQUALS, LOGICAL_AND,
        LOGICAL_OR,

        ASSIGN_ADD, ASSIGN_SUB, ASSIGN_MUL, ASSIGN_DIV,
        ASSIGN_MOD, ASSIGN_AND, ASSIGN_OR, ASSIGN_XOR,
        ASSIGN_LEFT_SHIFT, ASSIGN_RIGHT_SHIFT, ASSIGN_DECLARE,

        NUMBER, NAME, STRING, CHAR, NEWLINE
    }
    ignore = ' \t'

    literals = {'*', '/', '%', '&', '+', '-', '|', '^', '{', '}', '(', ')', '[', ']', ',', '.', '>', '<', ';', '?'}

    LEFT_SHIFT = r'<<'
    RIGHT_SHIFT = r'>>'
    EQUALS = r'=='
    NOT_EQUALS = 'r!='
    LESS_EQUALS = r'<='
    GREATER_EQUALS = r'>='
    LOGICAL_AND = r'&&'
    LOGICAL_OR = r'\|\|'

    ASSIGN_ADD = r'\+='
    ASSIGN_SUB = r'-='
    ASSIGN_MUL = r'\*='
    ASSIGN_DIV = r'\/='
    ASSIGN_MOD = r'%='
    ASSIGN_AND = r'&='
    ASSIGN_OR = r'\|='
    ASSIGN_XOR = r'\^='
    ASSIGN_LEFT_SHIFT = r'<<='
    ASSIGN_RIGHT_SHIFT = r'>>='
    ASSIGN_DECLARE = r':='

    NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'

    # Keywords
    NAME['break'] = BREAK
    NAME['const'] = CONST
    NAME['continue'] = CONTINUE
    NAME['defer'] = DEFER
    NAME['else'] = ELSE
    NAME['enum'] = ENUM
    NAME['fn'] = FN
    NAME['for'] = FOR
    NAME['go'] = GO
    NAME['goto'] = GOTO
    NAME['if'] = IF
    NAME['import'] = IMPORT
    NAME['in'] = IN
    NAME['interface'] = INTERFACE
    NAME['match'] = MATCH
    NAME['module'] = MODULE
    NAME['mut'] = MUT
    NAME['or'] = OR
    NAME['pub'] = PUB
    NAME['return'] = RETURN
    NAME['struct'] = STRUCT
    NAME['type'] = TYPE
    NAME['map'] = MAP
    NAME['assert'] = ASSERT
    NAME['true'] = TRUE
    NAME['false'] = FALSE

    @_(r"""("([^"\\]|\\.)*")|('([^'\\]|\\.)*')""")
    def STRING(self, t):
        t.value = t.value[1:-1]
        # TODO: Escaped stuff
        # TODO: String interpolation
        return t

    @_(r'`.`')
    def CHAR(self, t):
        return t[1:-1]

    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    @_(r'\/\/.*')
    def COMMENT(self, t):
        pass

    @_(r'[\r\n]+')
    def NEWLINE(self, t):
        self.lineno += t.value.count('\n')
        return t
