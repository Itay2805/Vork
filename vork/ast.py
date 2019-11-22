from typing import *
from enum import Enum

###################################################################################################################
# Forward declare stmts
###################################################################################################################


class VType:
    pass


class Stmt:
    pass


class StmtBlock(Stmt):

    def __init__(self, stmts: List[Stmt]):
        self.stmts = stmts

    def __str__(self, indent=''):
        s = '(block\n'
        indent += '  '
        for stmt in self.stmts:
            s += indent + str(stmt).replace('\n', '\n' + indent) + '\n'
        s = s[:-1]
        s += ')'
        return s


###################################################################################################################
# Expressions
###################################################################################################################


class Expr:
    pass


class ExprIntegerLiteral(Expr):

    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return str(self.value)


class ExprFloatLiteral(Expr):

    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return str(self.value)


class ExprIdentifierLiteral(Expr):

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class ExprBinary(Expr):

    def __init__(self, left: Expr, op: str, right: Expr):
        self.left = left
        self.right = right
        self.op = op

    def __str__(self):
        return f'({self.op} {self.left} {self.right})'


class ExprUnary(Expr):

    def __init__(self, op: str, right: Expr):
        self.right = right
        self.op = op

    def __str__(self):
        if self.op == '&':
            return f'(ref {self.right})'
        elif self.op == '*':
            return f'(deref {self.right})'
        else:
            return f'(prefix {self.op} {self.right})'


class ExprImplicitEnum(Expr):

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f'(implicit {self.name})'


class ExprIn(Expr):

    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right

    def __str__(self):
        return f'(in {self.left} {self.right})'


class ExprPostfix(Expr):

    def __init__(self, left: Expr, op: str):
        self.op = op
        self.left = left

    def __str__(self):
        return f'(postfix {self.left} {self.op})'


class ExprConditional(Expr):

    def __init__(self, condition: Expr, block_true: StmtBlock, block_false: StmtBlock):
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


class ExprMemberAccess(Expr):

    def __init__(self, value: Expr, member: str):
        self.value = value
        self.member = member

    def __str__(self):
        return f'(member {self.value} {self.member})'


class ExprIndexAccess(Expr):

    def __init__(self, value: Expr, index: Expr):
        self.value = value
        self.index = index

    def __str__(self):
        return f'(index {self.value} {self.index})'


class ExprCall(Expr):

    def __init__(self, func: Expr, args: List[Expr]):
        self.func = func
        self.args = args

    def __str__(self):
        return f'(call {self.func} ({" ".join(map(str, self.args))}))'


###################################################################################################################
# Statements
###################################################################################################################


class StmtExpr(Stmt):

    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return str(self.expr)


class StmtReturn(Stmt):

    def __init__(self, exprs: List[Expr]):
        self.exprs = exprs

    def __str__(self):
        return f'(return {" ".join(map(str, self.exprs))})'


class StmtAssert(Stmt):

    def __init__(self, expr: Expr):
        self.expr = expr

    def __str__(self):
        return f'(assert {self.expr})'


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


class StmtVarDecl(Stmt):

    def __init__(self, mut: bool, names: List[str], expr: Expr):
        self.mut = mut
        self.names = names
        self.expr = expr

    def __str__(self):
        mut = 'mut ' if self.mut else ''
        return f'(var {mut}({" ".join(self.names)}) {self.expr})'


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


class StmtUnsafe(Stmt):

    def __init__(self, block: StmtBlock):
        self.block = block

    def __str__(self):
        return '(unsafe\n  ' + str(self.block).replace('\n', '\n  ') + ')'


class StmtDefer(Stmt):

    def __init__(self, block: StmtBlock):
        self.block = block

    def __str__(self):
        return '(defer\n  ' + str(self.block).replace('\n', '\n  ') + ')'

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

    def __init__(self, pub: bool, interop: bool, name: str, method: FuncParam, args: List[FuncParam], ret_value: VType, block: StmtBlock):
        self.pub = pub
        self.interop = interop
        self.name = name
        self.method = method
        self.args = args
        self.ret_value = ret_value
        self.block = block

    def __str__(self):
        pub = 'pub ' if self.pub else ''
        block = str(self.block).replace("\n", "\n  ")
        ret_val = '' if self.ret_value is None else str(self.ret_value)
        name = ('C.' if self.interop else '') + self.name
        if self.block is not None:
            block = f'\n  {block}'
        else:
            block = ''
        method = str(self.method) + ' ' if self.method is not None else ''
        return f'(func {pub}{name} {method}({" ".join(map(str, self.args))}) {ret_val}{block})'


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
        self.pub = pub
        self.name = name
        self.value = value

    def __str__(self):
        pub = 'pub ' if self.pub else ''
        return f'(const {pub}{self.name} {self.value})'


###################################################################################################################
# Types
###################################################################################################################


class VUnknownType(VType):

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class VArrayType(VType):

    def __init__(self, xtype: VType):
        self.type = xtype

    def __str__(self):
        return f'[]{self.type}'


class VMapType(VType):

    def __init__(self, key_type: VType, value_type: VType):
        self.key_type = key_type
        self.value_type = value_type

    def __str__(self):
        return f'map[{self.key_type}]{self.value_type}'


class VOptionalType(VType):

    def __init__(self, xtype: VType):
        self.type = xtype

    def __str__(self):
        return f'?{self.type}'


class VPointerType(VType):

    def __init__(self, xtype: VType):
        self.type = xtype

    def __str__(self):
        return f'&{self.type}'
