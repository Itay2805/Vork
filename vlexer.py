from sly import Lexer


class VLexer(Lexer):
    tokens = {
        BREAK, CONST, CONTINUE, DEFER, ELSE, ENUM, FN,
        FOR, GO, GOTO, IF, IMPORT, IN, INTERFACE, MATCH,
        MODULE, MUT, OR, PUB, RETURN, STRUCT, TYPE, MAP,
        ASSERT,

        LEFT_SHIFT, RIGHT_SHIFT, EQUALS, NOT_EQUALS,
        LESS_EQUALS, GREATER_EQUALS, LOGICAL_AND,
        LOGICAL_OR,

        ASSIGN_ADD, ASSIGN_SUB, ASSIGN_MUL, ASSIGN_DIV,
        ASSIGN_MOD, ASSIGN_AND, ASSIGN_OR, ASSIGN_XOR,
        ASSIGN_LEFT_SHIFT, ASSIGN_RIGHT_SHIFT, ASSIGN_DECLARE,

        NUMBER, NAME, STRING, CHAR, NEWLINE
    }
    ignore = ' \t'

    literals = {'*', '/', '%', '&', '+', '-', '|', '^', '{', '}', '(', ')', '[', ']', ',', '.', '>', '<', ';'}

    # Keywords (should not have another letter afterwards)
    BREAK = r'break[^a-zA-Z0-9_]'
    CONST = r'const[^a-zA-Z0-9_]'
    CONTINUE = r'continue[^a-zA-Z0-9_]'
    DEFER = r'defer[^a-zA-Z0-9_]'
    ELSE = r'else[^a-zA-Z0-9_]'
    ENUM = r'enum[^a-zA-Z0-9_]'
    FN = r'fn[^a-zA-Z0-9_]'
    FOR = r'for[^a-zA-Z0-9_]'
    GO = r'go[^a-zA-Z0-9_]'
    GOTO = r'goto[^a-zA-Z0-9_]'
    IF = r'if[^a-zA-Z0-9_]'
    IMPORT = r'import[^a-zA-Z0-9_]'
    IN = r'in[^a-zA-Z0-9_]'
    INTERFACE = r'interface[^a-zA-Z0-9_]'
    MATCH = r'match[^a-zA-Z0-9_]'
    MODULE = r'module[^a-zA-Z0-9_]'
    MUT = r'mut[^a-zA-Z0-9_]'
    OR = r'or[^a-zA-Z0-9_]'
    PUB = r'pub[^a-zA-Z0-9_]'
    RETURN = r'return[^a-zA-Z0-9_]'
    STRUCT = r'struct[^a-zA-Z0-9_]'
    TYPE = r'type[^a-zA-Z0-9_]'
    MAP = r'map[^a-zA-Z0-9_]'
    ASSERT = r'assert[^a-zA-Z0-9_]'

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

    @_(r"""("([^"\\] | \\.) * ")|('([^'\\]|\\.)*')""")
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