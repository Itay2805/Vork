from enum import Enum


class UnknownCharacter(Exception):
    pass


class CodePosition:

    def __init__(self, start_line, end_line, start_column, end_column):
        self.start_line = start_line
        self.end_line = end_line
        self.start_column = start_column
        self.end_column = end_column


class Token:

    def __init__(self, pos: CodePosition):
        self.pos = pos

    def __repr__(self):
        raise NotImplementedError


class EofToken(Token):

    def __init__(self):
        super(EofToken, self).__init__(None)

    def __repr__(self):
        return f'<EofToken>'


class IntToken(Token):

    def __init__(self, pos: CodePosition, value: int):
        super(IntToken, self).__init__(pos)
        self.value = value

    def __repr__(self):
        return f'<IntToken: value={repr(self.value)}>'


class FloatToken(Token):

    def __init__(self, pos: CodePosition, value: float):
        super(FloatToken, self).__init__(pos)
        self.value = value

    def __repr__(self):
        return f'<FloatToken: value={repr(self.value)}>'


class IdentToken(Token):

    def __init__(self, pos: CodePosition, value: str):
        super(IdentToken, self).__init__(pos)
        self.value = value

    def __repr__(self):
        return f'<IdentToken: value={repr(self.value)}>'


class KeywordToken(Token):

    def __init__(self, pos: CodePosition, value: str):
        super(KeywordToken, self).__init__(pos)
        self.value = value

    def __repr__(self):
        return f'<KeywordToken: value={repr(self.value)}>'


class SymbolToken(Token):

    def __init__(self, pos: CodePosition, value: str):
        super(SymbolToken, self).__init__(pos)
        self.value = value

    def __repr__(self):
        return f'<SymbolToken: value={repr(self.value)}>'


class Tokenizer:

    def __init__(self, stream: str):
        self.stream = stream
        self.line = 0
        self.column = 0
        self.token = Token(None)

        self.before = []
        self.pushes = []

    def _inc_stream(self, times=1):
        # Increment the first thing
        while times > 0:
            was = self.stream[0]
            self.stream = self.stream[1:]
            if was == '\n':
                self.line += 1
                self.column = 0
            else:
                self.column += 1
            times -= 1

    def push(self):
        self.pushes.append([self.token])

    def pop(self):
        """
        Will take all the parsed elements since the push and
        add them back
        """
        items = self.pushes.pop()
        self.token = items[0]
        self.before = items[1:] + self.before

    def discard(self):
        """
        Remove the last push
        """
        self.pushes.pop()

    def is_token(self, kind) -> bool:
        if isinstance(kind, str):
            return isinstance(self.token, SymbolToken) and self.token.value == kind
        elif isinstance(self.token, kind):
            return True

    def is_keyword(self, ident) -> bool:
        if self.is_token(KeywordToken) and self.token.value == ident:
            return True
        else:
            return False

    def match_keyword(self, ident) -> bool:
        if self.is_keyword(ident):
            self.next_token()
            return True
        else:
            return False

    def match_token(self, kind) -> bool:
        if self.is_token(kind):
            self.next_token()
            return True
        else:
            return False

    def expect_token(self, kind):
        if self.is_token(kind):
            self.next_token()
        else:
            assert False, kind

    def expect_keyword(self, kind):
        if self.is_keyword(kind):
            self.next_token()
        else:
            assert False, kind

    def next_token(self):
        # We have items that have been saved
        if len(self.before) != 0:
            self.token = self.before[0]
            self.before = self.before[1:]

        # Parse a new item
        else:
            # Clear unneeded stuff
            while True:
                # Consume spaces
                if len(self.stream) > 0 and self.stream[0].isspace():
                    self._inc_stream()

                # Consume multiline comment
                elif len(self.stream) > 2 and self.stream[:2] == '/*':
                    self._inc_stream(2)
                    nesting = 1
                    while nesting > 0 and len(self.stream) > 0:
                        # Nested comment
                        if len(self.stream) > 2 and self.stream[:2] == '/*':
                            nesting += 1
                            self._inc_stream(2)
                        elif len(self.stream) > 1 and self.stream[:2] == '*/':
                            nesting -= 1
                            self._inc_stream(2)
                        self._inc_stream()

                # Consume one line comments
                elif len(self.stream) > 2 and self.stream[:2] == '//':
                    self._inc_stream(2)
                    while len(self.stream) > 0:
                        if self.stream[0] == '\n':
                            self._inc_stream()
                            break
                        self._inc_stream()

                # Nothing left to clear
                else:
                    break

            pos = CodePosition(self.line, self.line, self.column, self.column)

            # End of file
            if len(self.stream) == 0:
                self.token = EofToken()

            # Integers
            elif self.stream[0].isdigit():
                # Figure the base
                base = 10
                chars = '0123456789'
                if self.stream[0] == '0' and len(self.stream) > 3:
                    if self.stream[1].lower() == 'x':
                        base = 16
                        chars = '0123456789abcdefABCDEF'
                        self._inc_stream(2)
                    elif self.stream[1].lower() == 'b':
                        base = 2
                        chars = '01'
                        self._inc_stream(2)

                # TODO: octal numbers

                # Get the value and parse it
                value = ''
                while len(self.stream) > 0 and self.stream[0] in chars:
                    value += self.stream[0]
                    self._inc_stream()

                # Check if this will actually be a float
                # Only if the base is 10
                # TODO: more complete float expressions with e or whatever
                if base == 10 and len(self.stream) > 1 and self.stream[0] == '.' and self.stream[1].isdigit():
                    self._inc_stream()
                    after_dot = ''
                    while len(self.stream) > 0 and self.stream[0].isdigit():
                        after_dot += self.stream[0]
                        self._inc_stream()
                    self.token = FloatToken(pos, float(value + '.' + after_dot))
                else:
                    self.token = IntToken(pos, int(value, base))

            # Identifier token or keywords
            elif self.stream[0].isalpha() or self.stream[0] == '_':
                value = ''
                while len(self.stream) > 0 and (self.stream[0].isalnum() or self.stream[0] == '_'):
                    value += self.stream[0]
                    self._inc_stream()

                # Check if a keyword
                if value in [
                    'fn',
                    'pub',
                    'mut',
                    '__global',
                    'if',
                    'else',
                    'assert',
                    'for',
                    'in',
                    'match',
                    'enum',
                    'struct',
                    'interface',
                    'return',
                    'const',
                    'module',
                    'import',
                    'defer',
                    'go',
                    'or',
                    'continue',
                    'break',
                    'goto',
                    'type',
                    'unsafe',
                ]:
                    self.token = KeywordToken(pos, value)
                else:
                    self.token = IdentToken(pos, value)

            # Special characters
            elif self.stream[0] in '()[]{};\'",.:/*-+!%&<>=~^|':

                # Two character symbols
                if len(self.stream) > 1 and self.stream[:2] in [
                    '<<',
                    '>>',
                    '&&',
                    '||',
                    '!=',
                    '==',
                    '<=',
                    '>=',
                    '+=',
                    '-=',
                    '*=',
                    '/=',
                    '%=',
                    '&=',
                    '|=',
                    '^=',
                    '++',
                    '--',
                    ':=',
                ]:
                    self.token = SymbolToken(pos, self.stream[:2])
                    self._inc_stream(2)

                # Simple symbols
                else:
                    self.token = SymbolToken(pos, self.stream[0])
                    self._inc_stream()

            # Unknown
            else:
                raise UnknownCharacter()

            pos.end_column = self.column
            pos.end_line = self.line

        # Check if need to add to current save
        if len(self.pushes) != 0:
            self.pushes[-1].append(self.token)

        return self.token

