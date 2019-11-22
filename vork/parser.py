from vork.tokenizer import *
from vork.ast import *


class Parser:

    def __init__(self, tokenizer: Tokenizer):
        self.t = tokenizer
        self.t.next_token()

    ###################################################################################################################
    # Expression parsing
    #
    # See https://www.tutorialspoint.com/go/go_operators_precedence.htm for the table that I used as reference
    ###################################################################################################################

    def _parse_literal(self):
        if self.t.is_token(IntToken):
            val = self.t.token.value
            self.t.next_token()
            return ExprIntegerLiteral(val)

        elif self.t.is_token(FloatToken):
            val = self.t.token.value
            self.t.next_token()
            return ExprFloatLiteral(val)

        elif self.t.is_token(IdentToken):
            val = self.t.token.value
            self.t.next_token()
            return ExprIdentifierLiteral(val)

        elif self.t.match_token('('):
            expr = self.parse_expr()
            self.t.expect_token(')')
            return expr

        else:
            assert False, f'Unexpected token {self.t.token}'

    def _parse_postfix(self):
        expr = self._parse_literal()

        # Postfix operators
        if self.t.is_token('++') or self.t.is_token('--'):
            pass

        else:
            # Top level expressions
            while True:
                # Member access
                if self.t.match_token('.'):
                    assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
                    expr = ExprMemberAccess(expr, self.t.token.value)
                    self.t.next_token()

                # Function call
                elif self.t.match_token('('):
                    args = []
                    if not self.t.is_token(')'):
                        args = [self.parse_expr()]
                        while self.t.match_token(','):
                            args.append(self.parse_expr())
                    self.t.expect_token(')')
                    expr = ExprCall(expr, args)

                # Array access
                elif self.t.match_token('['):
                    expr = ExprIndexAccess(expr, self.parse_expr())
                    self.t.expect_token(']')

                # In expression
                elif self.t.match_keyword('in'):
                    expr = ExprIn(expr, self.parse_expr())

                # Nothing more, so we probably done
                else:
                    break

        return expr

    # TODO: deref (*), need to figure how to handle the ambiguity with multiplications
    def _parse_unary(self):

        # this can be done only one time
        if self.t.is_token('-') or self.t.is_token('--') or self.t.is_token('++') or self.t.is_token('&'):
            op = self.t.token.value
            self.t.next_token()
            expr = ExprUnary(op, self._parse_postfix())

        # These can be done multiple times
        elif self.t.is_token('!') or self.t.is_token('~') or self.t.is_token('*'):
            op = self.t.token.value
            self.t.next_token()
            expr = ExprUnary(op, self._parse_unary())

        # Implicit enum member access
        elif self.t.match_token('.'):
            assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
            name = self.t.token.value
            self.t.next_token()
            return ExprImplicitEnum(name)

        else:
            expr = self._parse_postfix()

        return expr

    def _parse_multiplicative(self):
        expr = self._parse_unary()

        while self.t.is_token('*') or self.t.is_token('/') or self.t.is_token('%'):
            op = self.t.token.value
            self.t.next_token()
            expr = ExprBinary(expr, op, self._parse_unary())

        return expr

    def _parse_additive(self):
        expr = self._parse_multiplicative()

        while self.t.is_token('+') or self.t.is_token('-'):
            op = self.t.token.value
            self.t.next_token()
            expr = ExprBinary(expr, op, self._parse_multiplicative())

        return expr

    def _parse_shift(self):
        expr = self._parse_additive()

        while self.t.is_token('<<') or self.t.is_token('>>'):
            op = self.t.token.value
            self.t.next_token()
            expr = ExprBinary(expr, op, self._parse_additive())

        return expr

    def _parse_relational(self):
        expr = self._parse_shift()

        while self.t.is_token('<') or self.t.is_token('>') or self.t.is_token('<=') or self.t.is_token('>='):
            op = self.t.token.value
            self.t.next_token()
            expr = ExprBinary(expr, op, self._parse_shift())

        return expr

    def _parse_equality(self):
        expr = self._parse_relational()

        while self.t.is_token('==') or self.t.is_token('!='):
            op = self.t.token.value
            self.t.next_token()
            expr = ExprBinary(expr, op, self._parse_relational())

        return expr

    def _parse_bitwise_and(self):
        expr = self._parse_equality()

        while self.t.match_token('&'):
            expr = ExprBinary(expr, '&', self._parse_equality())

        return expr

    def _parse_bitwise_xor(self):
        expr = self._parse_bitwise_and()

        while self.t.match_token('^'):
            expr = ExprBinary(expr, '^', self._parse_bitwise_and())

        return expr

    def _parse_bitwise_or(self):
        expr = self._parse_bitwise_xor()

        while self.t.match_token('|'):
            expr = ExprBinary(expr, '|', self._parse_bitwise_xor())

        return expr

    def _parse_logical_and(self):
        expr = self._parse_bitwise_or()

        while self.t.match_token('&&'):
            expr = ExprBinary(expr, '&&', self._parse_bitwise_or())

        return expr

    def _parse_logical_or(self):
        expr = self._parse_logical_and()

        while self.t.match_token('||'):
            expr = ExprBinary(expr, '||', self._parse_logical_and())

        return expr

    def _parse_conditional(self):
        if self.t.match_keyword('if'):
            condition = self.parse_expr()
            block_true = self.parse_stmt_block()

            assert self.t.match_keyword('else')
            block_false = self.parse_stmt_block()

            return ExprConditional(condition, block_true, block_false)
        else:
            return self._parse_logical_or()

    def _parse_assignment(self):
        expr = self._parse_conditional()

        while self.t.is_token('=') or self.t.is_token('+=') or self.t.is_token('-=') or self.t.is_token('*=') or \
                self.t.is_token('/=') or self.t.is_token('%=') or self.t.is_token('>>=') or self.t.is_token('<<=') or \
                self.t.is_token('&=') or self.t.is_token('^=') or self.t.is_token('|='):
            op = self.t.token.value
            self.t.next_token()

            if isinstance(expr, ExprBinary):
                expr = ExprBinary(expr.left, expr.op, ExprBinary(expr.right, op, self._parse_conditional()))
            else:
                expr = ExprBinary(expr, op, self._parse_conditional())

        return expr

    def parse_expr(self):
        return self._parse_assignment()

    # def parse_mut_expr(self):
    #     mut = False
    #     if self.t.match_keyword('mut'):
    #         mut = True
    #     return self.parse_expr(), mut

    ###################################################################################################################
    # Statement parsing
    ###################################################################################################################

    def _parse_var_decl(self):
        # Mutable optional
        mut = False
        if self.t.match_keyword('mut'):
            mut = True

        # Get the names
        assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
        names = [self.t.token.value]
        self.t.next_token()

        while self.t.match_token(','):
            assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
            names.append(self.t.token.value)
            self.t.next_token()

        # The :=
        self.t.expect_token(':=')

        # The assigned expression
        expr = self.parse_expr()

        return StmtVarDecl(mut, names, expr)

    def parse_stmt(self):
        # Return statement
        if self.t.match_keyword('return'):
            exprs = [self.parse_expr()]
            while self.t.match_token(','):
                exprs.append(self.parse_expr())
            return StmtReturn(exprs)

        # Assert statement
        elif self.t.match_keyword('assert'):
            return StmtAssert(self.parse_expr())

        # Parse if
        elif self.t.match_keyword('if'):
            condition = self.parse_expr()
            block_true = self.parse_stmt_block()
            block_false = None

            # Else part
            if self.t.match_keyword('else'):
                # We support `else if` without block before
                if self.t.is_keyword('if'):
                    block_false = StmtBlock([self.parse_stmt()])

                # The block
                else:
                    block_false = self.parse_stmt_block()

            return StmtIf(condition, block_true, block_false)

        # Block
        if self.t.is_token('{'):
            return self.parse_stmt_block()

        # For statement
        if self.t.match_keyword('for'):
            # Check if a foreach
            # will match (for name, name in test) and (for name in test)
            self.t.push()
            self.t.next_token()
            if self.t.is_token(','):
                self.t.pop()

                assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
                index = self.t.token.value
                self.t.next_token()

                self.t.expect_token(',')

                assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
                name = self.t.token.value
                self.t.next_token()

                self.t.expect_keyword('in')

                expr = self.parse_expr()
                block = self.parse_stmt_block()
                return StmtForeach(index, name, expr, block)

            elif self.t.is_keyword('in'):
                self.t.pop()

                assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
                name = self.t.token.value
                self.t.next_token()

                self.t.expect_keyword('in')

                expr = self.parse_expr()
                block = self.parse_stmt_block()
                return StmtForeach(None, name, expr, block)

            self.t.pop()

            # Check a forever loop
            if self.t.is_token('{'):
                block = self.parse_stmt_block()
                return StmtFor(None, None, None, block)

            # This is probably a normal c like loop
            else:
                val = None
                cond = None
                next = None

                # TODO: support `for condition` loops

                if not self.t.match_token(';'):
                    # TODO: variable declaration inside this argument
                    val = self.parse_expr()
                    self.t.expect_token(';')

                if not self.t.match_token(';'):
                    cond = self.parse_expr()
                    self.t.expect_token(';')

                if not self.t.is_token('{'):
                    next = self.parse_expr()

                block = self.parse_stmt_block()
                return StmtFor(val, cond, next, block)

        # Unsafe block
        if self.t.match_keyword('unsafe'):
            return StmtUnsafe(self.parse_stmt_block())

        # Defer block
        if self.t.match_keyword('defer'):
            return StmtDefer(self.parse_stmt_block())

        # Variable declaration
        if self.t.is_keyword('mut'):
            return self._parse_var_decl()

        # Might be variable declaration
        if self.t.is_token(IdentToken):
            self.t.push()
            self.t.next_token()

            # This verifies we got a variable declaration (a := ) or (a, b, c := )
            if self.t.is_token(':=') or self.t.is_token(','):
                self.t.pop()
                return self._parse_var_decl()
            else:
                self.t.pop()

        # Fallback on expression parsing
        return StmtExpr(self.parse_expr())

    def parse_stmt_block(self):
        self.t.expect_token('{')
        stmts = []
        while not self.t.match_token('}'):
            stmts.append(self.parse_stmt())
        return StmtBlock(stmts)

    ###################################################################################################################
    # Declaration parsing
    ###################################################################################################################

    def parse_type(self):
        # Map
        if self.t.match_keyword('map'):
            self.t.expect_token('[')
            key_type = self.parse_type()
            self.t.expect_token(']')
            value_type = self.parse_type()
            return VMapType(key_type, value_type)

        # Array
        if self.t.match_token('['):
            self.t.expect_token(']')
            value_type = self.parse_type()
            return VArrayType(value_type)

        # Optional type
        if self.t.match_token('?'):
            return VOptionalType(self.parse_type())

        # Pointer type
        if self.t.match_token('&'):
            return VPointerType(self.parse_type())

        # Basic type
        elif self.t.is_token(IdentToken):
            t = VUnknownType(self.t.token.value)
            self.t.next_token()
            return t

        else:
            assert False, "Invalid type"

    def _parse_func_param(self):
        assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
        name = self.t.token.value
        self.t.next_token()

        mut = False
        if self.t.match_keyword('mut'):
            mut = True

        xtype = self.parse_type()

        return FuncParam(mut, name, xtype)

    def _parse_func(self, pub):

        # Method (optional)
        method = None
        if self.t.match_token('('):
            method = self._parse_func_param()
            self.t.expect_token(')')

        # Name
        assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
        name = self.t.token.value
        self.t.next_token()

        interop = False
        if self.t.match_token('.'):
            assert name == 'C'
            assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
            interop = True
            name = self.t.token.value
            self.t.next_token()

        # Parameters
        self.t.expect_token('(')

        args = []

        # Parse arguments if any
        if not self.t.is_token(')'):
            args.append(self._parse_func_param())
            while self.t.match_token(','):
                args.append(self._parse_func_param())

        self.t.expect_token(')')

        # the return value
        ret_type = None
        if not self.t.is_token('{'):
            ret_type = self.parse_type()

        # The code
        if not interop:
            scope = self.parse_stmt_block()
        else:
            scope = None

        return FuncDecl(pub, interop, name, method, args, ret_type, scope)

    def _parse_struct_element(self, access: StructMemberAccess):
        assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
        name = self.t.token.value
        self.t.next_token()
        xtype = self.parse_type()
        return StructElement(access, name, xtype)

    def _parse_struct(self, pub):
        # Name
        assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
        name = self.t.token.value
        self.t.next_token()

        self.t.expect_token('{')

        access = StructMemberAccess.PRIVATE
        elements = []
        while not self.t.match_token('}'):
            # This is an access type
            if self.t.match_keyword('pub'):

                if self.t.match_keyword('mut'):
                    access = StructMemberAccess.PUBLIC_PRIV_MUT
                else:
                    access = StructMemberAccess.PUBLIC
                self.t.expect_token(':')

            elif self.t.match_keyword('mut'):
                access = StructMemberAccess.PRIVATE_MUT
                self.t.expect_token(':')

            elif self.t.match_keyword('__global'):
                access = StructMemberAccess.PUBLIC_MUT
                self.t.expect_token(':')

            # Probably just a member
            else:
                elements.append(self._parse_struct_element(access))

        return StructDecl(pub, name, None, elements)

    def _parse_import_name(self):
        assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
        name = self.t.token.value
        self.t.next_token()

        while self.t.match_token('.'):
            assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
            name += '.' + self.t.token.value
            self.t.next_token()

        return name

    def _parse_const(self, pub):
        assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
        name = self.t.token.value
        self.t.next_token()
        self.t.expect_token('=')
        expr = self.parse_expr()
        return ConstDecl(pub, name, expr)

    def _parse_enum(self, pub):
        assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
        name = self.t.token.value
        self.t.next_token()

        elements = []

        self.t.expect_token('{')
        while not self.t.match_token('}'):
            assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
            elements.append(self.t.token.value)
            self.t.next_token()

        return EnumDecl(pub, name, elements)

    def parse_decl(self, pub):
        # Anything which may be public
        if self.t.match_keyword('pub'):
            return self.parse_decl(True)

        # Parse function
        elif self.t.match_keyword('fn'):
            return self._parse_func(pub)

        # Struct declaration
        elif self.t.match_keyword('struct'):
            return self._parse_struct(pub)

        elif self.t.match_keyword('enum'):
            return self._parse_enum(pub)

        # Module declaration
        elif self.t.is_keyword('module'):
            assert not pub, "pub may not be used on module"
            self.t.next_token()

            assert self.t.is_token(IdentToken), f"Expected name, got {self.t.token}"
            mod = ModuleDecl(self.t.token.value)
            self.t.next_token()
            return mod

        # Import
        elif self.t.is_keyword('import'):
            assert not pub, "pub may not be used on import"
            self.t.next_token()

            # Multi import
            if self.t.match_token('('):
                imports = []
                while not self.t.match_token(')'):
                    imports.append(ImportDecl(self._parse_import_name()))
                return imports

            # Single import
            else:
                return ImportDecl(self._parse_import_name())

        # Constants
        elif self.t.match_keyword('const'):
            # Multi const decl
            if self.t.match_token('('):
                constants = []
                while not self.t.match_token(')'):
                    constants.append(self._parse_const(pub))
                return constants

            # Single const decl
            else:
                return self._parse_const(pub)

        else:
            assert False

    def parse(self):
        decls = []

        while not self.t.is_token(EofToken):
            res = self.parse_decl(False)
            if isinstance(res, list):
                for r in res:
                    decls.append(r)
            else:
                decls.append(res)

        return decls