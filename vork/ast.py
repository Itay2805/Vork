from typing import *
from enum import Enum


###################################################################################################################
# Forward declare stmts
###################################################################################################################


class VType:

    def __ne__(self, other):
        return not (self == other)


class Stmt:

    def type_checking(self, function):
        raise NotImplementedError


class Expr:

    def __init__(self):
        self.type = None  # type: VType

    def resolve_type(self, function):
        """
        :type function: FuncDecl
        """
        if self.type is None:
            self.type = self._internal_resolve_type(function)
            self.type = function.get_module().resolve_type(self.type)
        return self.type

    def _internal_resolve_type(self, function):
        """
        :type function: FuncDecl
        """
        raise NotImplementedError

###################################################################################################################
# Statements
###################################################################################################################


class StmtBlock(Stmt):

    def __init__(self, parent, stmts: List[Stmt]):
        """
        :type parent: StmtBlock or FuncDecl
        """
        self.vars = {}  # type: Dict[str, Tuple(VType, bool)]
        self.parent = parent
        self.stmts = stmts

    def __str__(self, indent=''):
        s = '(block\n'
        indent += '  '
        for stmt in self.stmts:
            s += indent + str(stmt).replace('\n', '\n' + indent) + '\n'
        s = s[:-1]
        s += ')'
        return s

    def get_var(self, name, search_parent: bool = True) -> Tuple[VType, bool] or None:
        if name not in self.vars:
            if search_parent:
                return self.parent.get_var(name)
            else:
                return None
        return self.vars[name]

    def add_var(self, name: str, type: VType, mut: bool):
        assert self.get_var(name) is None, f"variable {name} already exists in scope"
        self.vars[name] = type, mut

    def type_checking(self, function):
        function.push_frame(self)
        for stmt in self.stmts:
            stmt.type_checking(function)
        function.pop_frame()


class StmtExpr(Stmt):

    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return str(self.expr)

    def type_checking(self, function):
        self.expr.resolve_type(function)


class StmtReturn(Stmt):

    def __init__(self, exprs: List[Expr]):
        self.exprs = exprs

    def __str__(self):
        return f'(return {" ".join(map(str, self.exprs))})'

    def type_checking(self, function):
        assert len(self.exprs) <= 1, f'Multiple return values are not supported yet'

        for expr in self.exprs:
            expr.resolve_type(function)
            assert expr.type == function.ret_type, f'Type mismatch, expected `{function.ret_type}`, got `{expr.type}`'


class StmtAssert(Stmt):

    def __init__(self, expr: Expr):
        self.expr = expr

    def __str__(self):
        return f'(assert {self.expr})'

    def type_checking(self, function):
        assert isinstance(self.expr.resolve_type(function), VBool), f'assert requires a boolean expression'


class StmtIf(Stmt):

    def __init__(self, condition: Expr, block_true: StmtBlock, block_false: StmtBlock or None):
        self.condition = condition
        self.block_true = block_true
        self.block_false = block_false

    def __str__(self):
        s = f'(if {self.condition}'
        s += '\n  ' + str(self.block_true).replace('\n', '\n  ')
        if self.block_false is not None:
            s += '\n  else\n'
            s += '  ' + str(self.block_false).replace('\n', '\n  ')
        s += ')'
        return s

    def type_checking(self, function):
        assert isinstance(self.condition.resolve_type(function), VBool), f'if condition must be a boolean expression'
        self.block_true.type_checking(function)
        if self.block_false is not None:
            self.block_false.type_checking(function)


class StmtVarDecl(Stmt):

    def __init__(self, mut: bool, names: List[str], expr: Expr):
        self.mut = mut
        self.names = names
        self.expr = expr

    def __str__(self):
        mut = 'mut ' if self.mut else ''
        return f'(var {mut}({" ".join(self.names)}) {self.expr})'

    def type_checking(self, function):
        # TODO: support multiple return
        xtype = self.expr.resolve_type(function)
        function.frame[-1].add_var(self.names[0], xtype, self.mut)


class StmtForeach(Stmt):

    def __init__(self, index: str or None, name: str, list: Expr, block: StmtBlock):
        self.index = index
        self.name = name
        self.list = list
        self.block = block

    def __str__(self):
        name = ''
        if self.index is not None:
            name += self.index + ' '
        name += self.name
        s = f'(foreach {name} {self.list}\n'
        s += '  ' + str(self.block).replace('\n', '\n  ')
        s += ')'
        return s

    def type_checking(self, function):
        list_type = self.list.resolve_type(function)

        if isinstance(list_type, VArrayType):
            self.block.add_var(self.name, list_type.type, False)
            if self.index is not None:
                self.block.add_var(self.index, VIntegerType(32, True), False)

        elif isinstance(list_type, VMapType):
            self.block.add_var(self.name, list_type.value_type, False)
            if self.index is not None:
                self.block.add_var(self.index, list_type.key_type, False)

        else:
            assert False, f'Can not iterate over type `{list_type}`'

        self.block.type_checking(function)


class StmtFor(Stmt):

    def __init__(self, value: Expr or StmtVarDecl or None, condition: Expr or None, next: Expr or None, block: StmtBlock):
        self.value = value
        self.condition = condition
        self.next = next
        self.block = block

    def __str__(self):
        val = str(self.value) if self.value is not None else '()'
        cond = str(self.condition) if self.condition is not None else '()'
        next = str(self.next) if self.next is not None else '()'
        s = f'(for {val} {cond} {next}\n'
        s += '  ' + str(self.block).replace('\n', '\n  ')
        s += ')'
        return s

    def type_checking(self, function):
        if self.value is not None:

            if isinstance(self.value, Expr):
                self.value.resolve_type(function)

            elif isinstance(self.value, StmtVarDecl):
                self.value.type_checking(function)

            else:
                assert False

        if self.condition is not None:
            assert isinstance(self.condition.resolve_type(function), VBool), f'Condition of a for loop must be a boolean expression (got `{self.condition.resolve_type(function)}`)'

        if self.next is not None:
            self.next.resolve_type(function)

        self.block.type_checking(function)


class StmtUnsafe(Stmt):

    def __init__(self, block: StmtBlock):
        self.block = block

    def __str__(self):
        return '(unsafe\n  ' + str(self.block).replace('\n', '\n  ') + ')'

    def type_checking(self, function):
        self.block.type_checking(function)


class StmtDefer(Stmt):

    def __init__(self, block: StmtBlock):
        self.block = block

    def __str__(self):
        return '(defer\n  ' + str(self.block).replace('\n', '\n  ') + ')'

    def type_checking(self, function):
        self.block.type_checking(function)

###################################################################################################################
# Types
###################################################################################################################


class VUnknownType(VType):

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f'UnknownType<{self.name}>'


class VIntegerType(VType):

    def __init__(self, bits: int, signed: bool):
        self.bits = bits
        self.signed = signed

    def __str__(self):
        # Special cases
        if self.signed and self.bits == 32:
            return 'int'
        elif not self.signed and self.bits == 8:
            return 'byte'
        elif self.signed:
            return f'i{self.bits}'
        else:
            return f'u{self.bits}'

    def __eq__(self, other):
        if isinstance(other, VIntegerType):
            return self.signed == other.signed and self.bits == other.bits
        return False


class VFloatType(VType):

    def __init__(self, bits: int):
        self.bits = bits

    def __str__(self):
        return f'f{self.bits}'

    def __eq__(self, other):
        if isinstance(other, VFloatType):
            return self.bits == other.bits
        return False


class VBool(VType):

    def __init__(self):
        pass

    def __str__(self):
        return 'bool'

    def __eq__(self, other):
        return isinstance(other, VBool)


class VFuncType(VType):

    def __init__(self, args: List[Tuple[VType, bool]], ret: VType or None):
        self.args = args
        self.ret = ret

    def __str__(self):
        args = []
        for arg in self.args:
            a = ''
            if arg[1]:
                a += 'mut '
            a += arg[0]
            args.append(a)

        s = f'fn ({args})'

        if self.ret is not None:
            s += ' ' + self.ret

        return s

    def __eq__(self, other):
        if isinstance(other, VFuncType):
            return self.args == other.args and self.ret == other.ret
        return False


class VArrayType(VType):

    def __init__(self, xtype: VType):
        self.type = xtype

    def __str__(self):
        return f'[]{self.type}'

    def __eq__(self, other):
        if isinstance(other, VArrayType):
            return self.type == other.type
        return False


class VMapType(VType):

    def __init__(self, key_type: VType, value_type: VType):
        self.key_type = key_type
        self.value_type = value_type

    def __str__(self):
        return f'map[{self.key_type}]{self.value_type}'

    def __eq__(self, other):
        if isinstance(other, VMapType):
            return self.key_type == other.key_type and self.value_type == other.value_type
        return False


class VOptionalType(VType):

    def __init__(self, xtype: VType):
        self.type = xtype

    def __str__(self):
        return f'?{self.type}'

    def __eq__(self, other):
        if isinstance(other, VOptionalType):
            return self.type == other.type
        return False


class VPointerType(VType):

    def __init__(self, xtype: VType):
        self.type = xtype

    def __str__(self):
        return f'&{self.type}'

    def __eq__(self, other):
        if isinstance(other, VPointerType):
            return self.type == other.type
        return False


###################################################################################################################
# Expressions
###################################################################################################################


class ExprIntegerLiteral(Expr):

    def __init__(self, value: int):
        super(ExprIntegerLiteral, self).__init__()
        self.value = value

    def __str__(self):
        return str(self.value)

    def _internal_resolve_type(self, function):
        # Always an int
        return VIntegerType(32, True)


class ExprArrayLiteral(Expr):

    def __init__(self, values: List[Expr]):
        super(ExprArrayLiteral, self).__init__()
        self.values = values

    def __str__(self):
        s = '(array\n'
        s += '  ' + str(self.values).replace('\n', '\n  ') + ')'
        return s

    def _internal_resolve_type(self, function):
        array_type = None
        for element in self.values:
            type = element.resolve_type(function)
            if array_type is None:
                array_type = type
            else:
                assert type == array_type, f"Type mismatch in array literal, expected `{array_type}`, got `{type}`"
        return VArrayType(array_type)


class ExprRange(Expr):

    def __init__(self, expr_from: Expr, expr_to: Expr):
        super(ExprRange, self).__init__()
        self.expr_from = expr_from
        self.expr_to = expr_to

    def __str__(self):
        return f'(range {self.expr_from} {self.expr_to})'

    def _internal_resolve_type(self, function):
        from_type = self.expr_from.resolve_type(function)
        to_type = self.expr_to.resolve_type(function)
        assert from_type == to_type, f"Type mismatch ({from_type} and {to_type})"
        return VArrayType(from_type)


class ExprFloatLiteral(Expr):

    def __init__(self, value: int):
        super(ExprFloatLiteral, self).__init__()
        self.value = value

    def __str__(self):
        return str(self.value)

    def _internal_resolve_type(self, function):
        return VFloatType(32)


class ExprIdentifierLiteral(Expr):

    def __init__(self, name: str):
        super(ExprIdentifierLiteral, self).__init__()
        self.name = name

    def __str__(self):
        return self.name

    def _internal_resolve_type(self, function):
        res = function.get_var(self.name)
        assert res is not None, f"Unknown identifier `{self.name}`"
        var, mut = res
        return var


class ExprBinary(Expr):

    TYPE_TABLE = {
        '+': [VIntegerType, VFloatType],
        '-': [VIntegerType, VFloatType],
        '*': [VIntegerType, VFloatType],
        '/': [VIntegerType, VFloatType],
        '%': [VIntegerType],

        '&': [VIntegerType],
        '|': [VIntegerType],
        '^': [VIntegerType],

        # TODO: restrict with unsigned numbers on the right
        '<<': [VIntegerType],
        '>>': [VIntegerType],

        '&&': [VBool],
        '||': [VBool],
    }

    def __init__(self, left: Expr, op: str, right: Expr):
        super(ExprBinary, self).__init__()
        self.left = left
        self.right = right
        self.op = op

    def __str__(self):
        return f'({self.op} {self.left} {self.right})'

    def _internal_resolve_type(self, function):
        left_type = self.left.resolve_type(function)
        right_type = self.right.resolve_type(function)
        assert left_type == right_type, f"Mismatching types (`{left_type}` and `{right_type}`)"

        # This is part of assignment?
        if self.op.endswith('='):

            # relational and equality
            if len(self.op) == 2 and self.op[0] in ['>', '<', '=', '!']:
                return VBool()

            # Assignment expression
            else:
                assert left_type.__class__ in ExprBinary.TYPE_TABLE[self.op[-1]], f'Invalid type `{left_type}` for operator `{self.op[-1]}`'
                return left_type

        # Normal operators
        else:
            assert left_type.__class__ in ExprBinary.TYPE_TABLE[
                self.op[-1]], f'Invalid type `{left_type}` for operator `{self.op}`'
            return left_type


class ExprUnary(Expr):

    def __init__(self, op: str, right: Expr):
        super(ExprUnary, self).__init__()
        self.right = right
        self.op = op

    def __str__(self):
        if self.op == '&':
            return f'(ref {self.right})'
        elif self.op == '*':
            return f'(deref {self.right})'
        else:
            return f'(prefix {self.op} {self.right})'

    def _internal_resolve_type(self, function):
        xtype = self.right.resolve_type(function)

        if self.op == '*':
            assert isinstance(xtype, VPointerType), f"Tried to dereference a none pointer (`{xtype}`)"
            return xtype.type

        elif self.op == '&':
            # TODO: check that it is possible to ref the expression
            return VPointerType(xtype)

        elif self.op == '!':
            assert isinstance(xtype, VBool), f'Invalid type `{xtype}` for operator `{self.op}`'
            return xtype

        elif self.op == '~':
            assert isinstance(xtype, VIntegerType), f'Invalid type `{xtype}` for operator `{self.op}`'
            return xtype

        else:
            assert isinstance(xtype, VIntegerType) or isinstance(xtype, VFloatType), f'Invalid type `{xtype}` for operator `{self.op}`'
            return xtype


class ExprImplicitEnum(Expr):

    def __init__(self, name: str):
        super(ExprImplicitEnum, self).__init__()
        self.name = name

    def __str__(self):
        return f'(implicit {self.name})'

    def _internal_resolve_type(self, function):
        assert False, "Implicit enums are not supported yet"


class ExprIn(Expr):

    def __init__(self, left: Expr, right: Expr):
        super(ExprIn, self).__init__()
        self.left = left
        self.right = right

    def __str__(self):
        return f'(in {self.left} {self.right})'

    def _internal_resolve_type(self, function):
        left_type = self.left.resolve_type(function)
        right_type = self.left.resolve_type(function)

        if isinstance(right_type, VMapType):
            assert left_type == right_type.key_type, f"Type mismatch, expected {right_type.key_type}, got {left_type}"

        elif isinstance(right_type, VArrayType):
            assert left_type == VIntegerType(32, True), f"Type mismatch, expected {right_type.type}, got {left_type}"

        return VBool()


class ExprPostfix(Expr):

    def __init__(self, left: Expr, op: str):
        super(ExprPostfix, self).__init__()
        self.op = op
        self.left = left

    def __str__(self):
        return f'(postfix {self.left} {self.op})'

    def _internal_resolve_type(self, function):
        xtype = self.left.resolve_type(function)
        assert isinstance(xtype, VIntegerType), f'Invalid type `{xtype}` for operator `{self.op}`'
        return xtype


class ExprIf(Expr):

    def __init__(self, condition: Expr, block_true: StmtBlock, block_false: StmtBlock):
        super(ExprIf, self).__init__()
        self.condition = condition
        self.block_true = block_true
        self.block_false = block_false

    def __str__(self):
        s = f'(if {self.condition}\n'
        s += '  ' + str(self.block_true).replace('\n', '\n  ') + '\n'
        s += '  else\n'
        s += '  ' + str(self.block_false).replace('\n', '\n  ')
        s += ')'
        return s

    def _internal_resolve_type(self, function):
        self.block_true.type_checking(function)
        self.block_false.type_checking(function)

        assert len(self.block_true.stmts) != 0 and isinstance(self.block_true.stmts[-1], StmtExpr), f'Last statement of an if expression must be an expression!'
        assert len(self.block_false.stmts) != 0 and isinstance(self.block_false.stmts[-1], StmtExpr), f'Last statement of an if expression must be an expression!'

        true_type = self.block_true[-1].expr.resolve_type(function)
        false_type = self.block_true[-1].expr.resolve_type(function)
        assert true_type == false_type, f'Type mismatch between blocks (got {true_type} and {false_type})'

        return true_type


class ExprOr(Expr):

    def __init__(self, expr: Expr, block_error: StmtBlock):
        super(ExprOr, self).__init__()
        self.expr = expr
        self.block_error = block_error

    def __str__(self):
        s = f'(or {self.expr}\n'
        s += '  ' + str(self.block_error).replace('\n', '\n  ') + ')'
        return s

    def _internal_resolve_type(self, function):
        xtype = self.expr.resolve_type(function)
        assert isinstance(xtype, VOptionalType), f'expected an optional type, got `{xtype}`'

        # Make sure the block never exits the block
        # TODO: add check for the panic function (or just add a noreturn attribute?)
        self.block_error.type_checking(function)
        assert len(self.block_error.stmts) != 0, f'or block must return!'
        stmt = self.block_error.stmts[-1]
        assert isinstance(stmt, StmtReturn), f'or block must return!'

        # Return the underlying type
        return xtype.type


class ExprMemberAccess(Expr):

    def __init__(self, value: Expr, member: str):
        super(ExprMemberAccess, self).__init__()
        self.value = value
        self.member = member

    def __str__(self):
        return f'(member {self.value} {self.member})'

    def _internal_resolve_type(self, function):
        value_type = self.value.resolve_type(function)

        # Enum members
        if isinstance(value_type, EnumDecl):
            assert self.member in value_type.elements, f'Unknown enum field `{self.member}`'

            # TODO: check pub access

            return value_type

        # Struct members
        elif isinstance(value_type, StructDecl):
            for elem in value_type.elements:
                # TODO: access checks
                if elem.name == self.member:
                    return elem.type

            assert False, f"Unknown struct field `{self.member}`"

        # Array type, these are hardcoded
        elif isinstance(value_type, VArrayType):
            if self.member == 'data':
                # TODO: voidptr
                assert False

            elif self.member == 'len':
                return VIntegerType(32, True)

            elif self.member == 'cap':
                return VIntegerType(32, True)

            elif self.member == 'element_size':
                return VIntegerType(32, True)

            else:
                assert False, f'Unknown array field `{self.member}`'

        # Map type, these are hardcoded
        elif isinstance(value_type, VMapType):
            if self.member == 'size':
                return VIntegerType(32, True)

            else:
                assert False, f'Unknown map field `{self.member}`'

        # TODO: string type

        # TODO: Search for methods

        # Interops (should be)
        elif isinstance(value_type, dict):
            if self.member in value_type:
                return value_type[self.member]
            else:
                assert False, f'Unknown interop function `{self.member}`'

        # Did not find anything
        assert False, f'Type `{self.member}` has no members!'


class ExprIndexAccess(Expr):

    def __init__(self, value: Expr, index: Expr):
        super(ExprIndexAccess, self).__init__()
        self.value = value
        self.index = index

    def __str__(self):
        return f'(index {self.value} {self.index})'

    def _internal_resolve_type(self, function):
        value_type = self.value.resolve_type(function)
        index_type = self.index.resolve_type(function)

        if isinstance(value_type, VArrayType):
            assert index_type == VIntegerType(32, True), f'Type mismatch, expected `int`, got `{index_type}`'
            return value_type.type

        elif isinstance(value_type, VMapType):
            assert index_type == value_type.key_type, f"Type mistmatch, expected `{value_type.key_type}`, got `{index_type}`"
            return value_type.value_type

        else:
            assert False, f"type `{value_type}` is not index-able"


class ExprCall(Expr):

    def __init__(self, func: Expr, args: List[Expr]):
        super(ExprCall, self).__init__()
        self.func = func
        self.args = args

    def __str__(self):
        return f'(call {self.func} ({" ".join(map(str, self.args))}))'

    def _internal_resolve_type(self, function):
        func_type = self.func.resolve_type(function)

        assert isinstance(func_type, FuncDecl), f'Not a function!'
        assert len(func_type.args) == len(self.args), f'Function expected {len(func_type.args)} arguments, got {len(self.args)}'

        for i in range(len(func_type.args)):
            expect_arg_type = func_type.args[i].type
            arg_type = self.args[i].resolve_type(function)
            assert arg_type == arg_type, f'Type mismatch, expected `{func_type.args[i]}`, got `{arg_type}`'

        return func_type.ret_type

###################################################################################################################
# Declarations
###################################################################################################################


class FuncParam:

    def __init__(self, mut: bool, name: str, xtype: VType):
        self.mut = mut
        self.name = name
        self.type = xtype

    def __str__(self):
        mut = 'mut ' if self.mut else ''
        return f'({mut}{self.name} {self.type})'


class FuncDecl:

    def __init__(self, pub: bool, interop: bool, name: str, method: FuncParam, args: List[FuncParam], ret_value: VType):
        self.module = None  # type: Module
        self.pub = pub
        self.interop = interop
        self.name = name
        self.method = method
        self.args = args
        self.ret_type = ret_value
        self.block = None  # type: StmtBlock or None
        self.frame = []  # type: List[StmtBlock]

    def __str__(self):
        pub = 'pub ' if self.pub else ''
        block = str(self.block).replace("\n", "\n  ")
        ret_val = '' if self.ret_type is None else str(self.ret_type)
        name = ('C.' if self.interop else '') + self.name
        if self.block is not None:
            block = f'\n  {block}'
        else:
            block = ''
        method = str(self.method) + ' ' if self.method is not None else ''
        return f'(func {pub}{name} {method}({" ".join(map(str, self.args))}) {ret_val}{block})'

    def type_checking(self):
        if self.block is not None:
            self.block.type_checking(self)

    def get_module(self):
        assert self.module is not None
        return self.module

    def push_frame(self, block):
        self.frame.append(block)

    def pop_frame(self):
        self.frame.pop()

    def get_var(self, name):
        # Check for the stack frames first
        for frame in self.frame:
            f = frame.get_var(name, False)
            if f is not None:
                return f

        # Then check for the args
        for arg in self.args:
            if arg.name == name:
                return arg.type, arg.mut

        # Lastly check from the module
        return self.module.get_var(name)


class StructMemberAccess(Enum):
    PRIVATE = 'private'
    PRIVATE_MUT = 'private mut'
    PUBLIC = 'public'
    PUBLIC_PRIV_MUT = 'public, private mut'
    PUBLIC_MUT = 'public mut'


class StructElement:

    def __init__(self, access: StructMemberAccess, name: str, xtype: VType):
        self.access = access
        self.name = name
        self.type = xtype

    def __str__(self):
        return f'({self.access.value} {self.name} {self.type})'


class StructDecl:

    def __init__(self, pub: bool, name: str, base: StructElement or None, elements: List[StructElement]):
        self.module = None  # type: Module
        self.pub = pub
        self.name = name
        self.base = base
        self.elements = elements

    def __str__(self):
        pub = 'pub ' if self.pub else ''

        s = f'(struct {pub}{self.name}\n'

        if self.base is not None:
            s += '  ' + str(self.base) + '\n'

        for elem in self.elements:
            s += '  ' + str(elem) + '\n'

        s = s[:-1]
        s += ')'
        return s


class ModuleDecl:

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f'(module {self.name})'


class ImportDecl:

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f'(import {self.name})'


class EnumDecl:

    def __init__(self, pub: bool, name: str, elements: List[str]):
        self.module = None  # type: Module
        self.pub = pub
        self.name = name
        self.elements = elements

    def __str__(self):
        pub = 'pub ' if self.pub else ''
        s = f'(enum {pub}{self.name}\n'
        i = 0
        for elem in self.elements:
            s += f'  ({i} {elem})\n'
            i += 1
        s = s[:-1]
        s += ')'
        return s


class ConstDecl:

    def __init__(self, pub: bool, name: str, value: Expr):
        self.module = None  # type: Module
        self.pub = pub
        self.name = name
        self.value = value

    def __str__(self):
        pub = 'pub ' if self.pub else ''
        return f'(const {pub}{self.name} {self.value})'

    def type_checking(self):
        self.value.resolve_type(self.module)

    def get_type(self, function):
        return self.value.resolve_type(self.module)


class Module:

    TYPE_MAP = {
        'i8': VIntegerType(8, True),
        'i16': VIntegerType(16, True),
        'int': VIntegerType(32, True),
        'i64': VIntegerType(64, True),
        'i128': VIntegerType(128, True),

        'byte': VIntegerType(8, False),
        'u16': VIntegerType(16, False),
        'u32': VIntegerType(32, False),
        'u64': VIntegerType(64, False),
        'u128': VIntegerType(128, False),

        'f32': VFloatType(32),
        'f64': VFloatType(64),

        'bool': VBool(),

        # 'byteptr':
        # 'voidptr':
        #
        # 'string':
        # 'rune':
    }

    def __init__(self):
        self.name = 'main'
        self.decls = {
            'C': {}
        }  # type: Dict[str, Any]

        # interop functions are added to this scope

    def add(self, val):
        assert val.name not in Module.TYPE_MAP, f'duplicate name `{val.name}` in module `{self.name}`'
        if not isinstance(val, Module):
            val.module = self

        # Handle interop functions properly
        if isinstance(val, FuncDecl):
            if val.interop:
                assert val.name not in self.decls['C'], f'duplicate name `{val.name}` in module `{self.name}`'
                self.decls['C'][val.name] = val
            else:
                assert val.name not in self.decls, f'duplicate name `{val.name}` in module `{self.name}`'
                self.decls[val.name] = val
        else:
            self.decls[val.name] = val

    def get_var(self, name):
        if name in self.decls:
            return self.decls[name], False
        return None

    def resolve_type(self, xtype):

        # Unknown type
        if isinstance(xtype, VUnknownType):
            if xtype.name in Module.TYPE_MAP:
                return Module.TYPE_MAP[xtype.name]
            else:
                assert False, f'Unknown type `{xtype.name}`'

        # Array ty[e
        elif isinstance(xtype, VArrayType):
            xtype.type = self.resolve_type(xtype.type)

        # Map type
        elif isinstance(xtype, VMapType):
            xtype.key_type = self.resolve_type(xtype.key_type)
            xtype.value_type = self.resolve_type(xtype.value_type)

        # Pointer type
        elif isinstance(xtype, VPointerType):
            xtype.type = self.resolve_type(xtype.type)

        # Optional type
        elif isinstance(xtype, VOptionalType):
            xtype.type = self.resolve_type(xtype.type)

        # Default types, nothing more to resolve
        elif isinstance(xtype, VIntegerType) or isinstance(xtype, VFloatType) or isinstance(xtype, VBool):
            pass

        # Enums and structs are already resovled
        elif isinstance(xtype, EnumDecl) or isinstance(xtype, StructDecl) or isinstance(xtype, FuncDecl):
            pass

        # Handle a dictionary
        elif isinstance(xtype, dict):
            for key in xtype:
                xtype[key] = self.resolve_type(xtype[key])

        # No return value
        elif xtype is None:
            return None

        else:
            assert False, xtype

        return xtype

    def get_module(self):
        return self

    def type_checking(self):
        structs = []
        constants = []
        functions = []

        # add to lists everything we will need to resolve
        for r in self.decls:
            decl = self.decls[r]
            if isinstance(decl, StructDecl):
                structs.append(decl)
            elif isinstance(decl, ConstDecl):
                constants.append(decl)
            elif isinstance(decl, FuncDecl):
                functions.append(decl)

        # TODO: Functions should return a func type!

        # Resolve all the interop stuff
        for r in self.decls['C']:
            r = self.decls['C'][r]
            if isinstance(r, FuncDecl):
                for arg in r.args:
                    arg.type = self.resolve_type(arg.type)

                if r.ret_type is not None:
                    r.ret_type = self.resolve_type(r.ret_type)

        # Resolve all the constants
        for const in constants:
            const.type_checking()

        # Resolve all of the types inside of functions
        for func in functions:
            for arg in func.args:
                arg.type = self.resolve_type(arg.type)

            if func.ret_type is not None:
                func.ret_type = self.resolve_type(func.ret_type)

        # finally do type checking on all functions
        for func in functions:
            func.type_checking()
