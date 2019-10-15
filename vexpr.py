from vast import *
from vtypes import default_value_for_type


class TypeCheckError(BaseException):

    def __init__(self, report, msg, func):
        self.report = report
        self.msg = msg
        self.func = func


def default_assertion(xtype, report, func):
    """
    Run these in most expressions

    These make sure the type is not void nor multiple return
    """
    if isinstance(xtype, list):
        raise TypeCheckError(report, "Expression can not take multiple return", func)
    if isinstance(xtype, VVoidType):
        raise TypeCheckError(report, "Expression can not take void return", func)


class ExprIntegerLiteral(Expr):

    def __init__(self, num, report):
        """
        :type num: int
        """
        super(ExprIntegerLiteral, self).__init__(report)
        self.num = num

    def resolve_type(self, module, scope):
        """
        :type module: VModule
        :type scope: StmtCompound
        :rtype: VType
        """

        # Always return a type of int, to override it use the casts
        return module.resolve_type(VInt)

    def is_mut(self, module, scope):
        return True

    def __str__(self):
        return str(self.num)


class ExprBoolLiteral(Expr):

    def __init__(self, b, report):
        """
        :type b: bool
        """
        super(ExprBoolLiteral, self).__init__(report)
        self.b = b

    def resolve_type(self, module, scope):
        return module.resolve_type(VBool())

    def is_mut(self, module, scope):
        return True

    def __str__(self):
        return str(self.b).lower()


# TODO: We can probably just use the other struct literal
class ExprStructLiteralNamed(Expr):

    def __init__(self, ref, xtype, fields, report):
        """
        :type ref: bool
        :type xtype: VStructType
        :type fields: List[Tuple[str, Expr]]
        """
        super(ExprStructLiteralNamed, self).__init__(report)
        self.ref = ref
        self.xtype = xtype
        self.fields = fields

    def resolve_type(self, module, scope):
        # Don't forget to resolve it
        self.xtype = module.resolve_type(self.xtype)  # type: VStructType

        fields = self.fields

        if len(self.fields) == len(self.xtype.fields):
            raise TypeCheckError(self.report, f"expected {len(self.xtype.fields)} fields in struct initialization, got {len(self.fields)}", scope.get_function().name)

        # TODO: Embedded type

        for i in range(len(self.fields)):
            field_name = fields[i][0]
            expr = fields[i][1]
            struct_field = self.xtype.get_field(field_name)

            # Check the initialization type
            t = expr.resolve_type(module, scope)
            if t != struct_field.xtype:
                raise TypeCheckError(expr.report, f"field `{struct_field.name}` requires `{struct_field.xtype}`, got `{t}`", scope.get_function().name)

            # If this is a private field only the same module can initialize it
            if struct_field.access_mod == ACCESS_PRIVATE or struct_field.access_mod == ACCESS_PRIVATE_MUT:
                if scope.get_function().get_module() != self.xtype.module:
                    raise TypeCheckError(expr.report, f"can not initialize field `{struct_field.name}` (set as private)", scope.get_function().name)

        # return the struct type
        if self.ref:
            return module.add_type(VRef(self.xtype), self.report)

        return module.add_type(self.xtype, self.report)

    def is_mut(self, module, scope):
        return True


class ExprStructLiteral(Expr):

    def __init__(self, ref, xtype, fields, report):
        """
        :type ref: bool
        :type xtype: VStructType
        :type fields: List[Expr]
        """
        super(ExprStructLiteral, self).__init__(report)
        self.ref = ref
        self.xtype = xtype
        self.fields = fields

    def resolve_type(self, module, scope):
        # Don't forget to resolve it
        self.xtype = module.resolve_type(self.xtype)  # type: VStructType

        if len(self.fields) != len(self.xtype.fields):
            raise TypeCheckError(self.report, f"expected {len(self.xtype.fields)} fields in struct initialization, got {len(self.fields)}", scope.get_function().name)

        # TODO: Embedded type

        for i in range(len(self.fields)):
            struct_field = self.xtype.fields[i]
            expr = self.fields[i]

            # Check the initialization type
            t = expr.resolve_type(module, scope)
            if t != struct_field.xtype:
                raise TypeCheckError(expr.report, f"field `{struct_field.name}` requires `{struct_field.xtype}`, got `{t}`", scope.get_function().name)

            # If this is a private field only the same module can initialize it
            if struct_field.access_mod == ACCESS_PRIVATE or struct_field.access_mod == ACCESS_PRIVATE_MUT:
                if scope.get_function().get_module() != self.xtype.module:
                    raise TypeCheckError(f"can not initialize field `{struct_field.name}` (set as private)", scope.get_function().name)

        # return the struct type
        if self.ref:
            return module.add_type(VRef(self.xtype), self.report)

        return module.add_type(self.xtype, self.report)

    def is_mut(self, module, scope):
        return True

    # TODO: This
    # def __str__(self):
    #     pass


class ExprIdentifierLiteral(Expr):

    def __init__(self, name, report):
        super(ExprIdentifierLiteral, self).__init__(report)
        self.name = name

    def resolve_type(self, module, scope):
        ident = scope.get_identifier(self.name)
        if ident is None:
            raise TypeCheckError(self.report, f"Unknown identifier `{self.name}`", scope.get_function().name)

        if isinstance(ident, VFunction) or isinstance(ident, VInteropFunction):
            return ident.type

        elif isinstance(ident, VVariable):
            return ident.type

        elif isinstance(ident, VType):
            return ident

        elif isinstance(ident, VModule):
            return ident

        elif isinstance(ident, dict):
            return ident

        else:
            assert False, f"Unexpected identifier type {ident.__class__}"

    def is_mut(self, module, scope):
        ident = scope.get_identifier(self.name)

        if isinstance(ident, VFunction) or isinstance(ident, VInteropFunction):
            return False

        elif isinstance(ident, VVariable):
            return ident.mut

        elif isinstance(ident, VType):
            return False

        else:
            assert False, f"Unexpected identifier type {ident.__class__}"

    def __str__(self):
        return self.name


class ExprBinary(Expr):

    POSSIBLE_TYPES = {
        '+': [VIntegerType],
        '-': [VIntegerType],
        '*': [VIntegerType],
        '/': [VIntegerType],
        '%': [VIntegerType],

        '&': [VIntegerType],
        '|': [VIntegerType],
        '^': [VIntegerType],

        '&&': [VBool],
        '||': [VBool],

        '>>': [VIntegerType],
        '<<': [VIntegerType],

        '==': ([VIntegerType, VBool], VBool()),
        '!=': ([VIntegerType, VBool], VBool()),
        '>=': ([VIntegerType, VBool], VBool()),
        '>':  ([VIntegerType, VBool], VBool()),
        '<=': ([VIntegerType, VBool], VBool()),
        '<':  ([VIntegerType, VBool], VBool()),
    }

    def __init__(self, op, left_expr, right_expr, report):
        """
        :type op: str
        :type left_expr: Expr
        :type right_expr: Expr
        """
        super(ExprBinary, self).__init__(report)
        self.op = op
        self.left_expr = left_expr
        self.right_expr = right_expr

    def resolve_type(self, module, scope):
        t0 = self.left_expr.resolve_type(module, scope)
        t1 = self.right_expr.resolve_type(module, scope)

        default_assertion(t0, self.left_expr.report, scope.get_function().name)
        default_assertion(t1, self.right_expr.report, scope.get_function().name)

        # The types need to be the same
        # TODO: have this add casts or something
        if t0 != t1:
            raise TypeCheckError(self.report, f'Binary operators must have the same type on both sides (got `{t0}` and `{t1}`)', scope.get_function().name)

        # Make sure we can use the operator on the given type
        good = False
        types = self.POSSIBLE_TYPES[self.op]

        # Type override
        got_type = t0
        if isinstance(types, tuple):
            got_type = types[1]
            types = types[0]

        # Check if fitting
        for xtype in types:
            if isinstance(t0, xtype):
                good = True
                break

        # TODO: Check for operator overloading functions

        if not good:
            raise TypeCheckError(self.report, f"Binary operator `{self.op}` can't be used on `{t0.__class__.__name__}`", scope.get_function().name)

        return got_type

    def is_mut(self, module, scope):
        return True

    def __str__(self):
        return f'{self.left_expr} {self.op} {self.right_expr}'


class ExprFunctionCall(Expr):
    """
    Will call the given function returning either a single value or multiple values
    """

    def __init__(self, func_expr, arguments, report):
        """
        :type func_expr: Expr
        :type arguments: List[Tuple(bool, Expr)]
        """
        super(ExprFunctionCall, self).__init__(report)
        self.func_expr = func_expr
        self.arguments = arguments

    def resolve_type(self, module, scope):
        func = self.func_expr.resolve_type(module, scope)
        default_assertion(func, self.func_expr.report, scope.get_function().name)

        # Nomral functions
        if isinstance(func, VFunctionType):
            assert len(self.arguments) == len(func.param_types), f"expected {len(func.param_types)} arguments, got {len(self.arguments)}"
            for i in range(len(self.arguments)):
                from_mut = self.arguments[i][0]
                from_expr = self.arguments[i][1]
                from_type = from_expr.resolve_type(module, scope)
                to_mut = func.param_types[i][1]
                to_type = func.param_types[i][0]
                if from_type != to_type:
                    raise TypeCheckError(from_expr.report, f'function agument at `{i}` expected `{to_type}`, got `{from_type}`', scope.get_function().name)

                if to_mut != from_mut:
                    raise TypeCheckError(from_expr.report, f'function agument at `{i}` expected mut to be `{to_mut}`, got `{from_mut}`', scope.get_function().name)

                # Check if has the `mut` modifier on function call
                if from_mut:
                    if from_mut != from_expr.is_mut(module, scope):
                        raise TypeCheckError(from_expr.report, f'tried to convert mut `{from_mut}`, got `{from_expr.is_mut(module, scope)}`', scope.get_function().name)

            # If returns one type, return 1 type
            if len(func.return_types) == 1:
                return func.return_types[0]

            # If does not return anything, return void type
            elif len(func.return_types) == 0:
                return VVoidType()

            # If has multiple types just return them all
            # TODO: make sure to handle list of types everywhere
            else:
                return func.return_types

        # int casts
        elif isinstance(func, VIntegerType):
            assert len(self.arguments) == 1, f"expected 1 argument for cast, got {len(self.arguments)}"
            t = self.arguments[0][1].resolve_type(module, scope)
            assert isinstance(t, VIntegerType), f"Integer cast requires an integer (got `{t}`)"
            return func

        else:
            assert False, f"the type `{func}` is not callable"

    def is_mut(self, module, scope):
        func = self.func_expr.resolve_type(module, scope)
        if isinstance(func, VFunctionType):
            if len(func.return_types) > 1:
                return [True] * len(func.return_types)

            elif len(func.return_types) == 1:
                return True

            else:
                return False

        elif isinstance(func, VIntegerType):
            return True

        assert False

    def __str__(self):
        args = ', '.join(['mut ' if arg[0] else '' + str(arg[1]) for arg in self.arguments])
        return f'{self.func_expr}({args})'


class ExprMemberAccess(Expr):
    """
    Will return the member of the given expression
    """

    def __init__(self, expr, member_name, report):
        """
        :type expr: Expr
        :type member_name: str
        """
        super(ExprMemberAccess, self).__init__(report)
        self.expr = expr
        self.member_name = member_name

    def resolve_type(self, module, scope):
        t = self.expr.resolve_type(module, scope)
        default_assertion(t, self.expr.report, scope.get_function().name)

        # This a struct
        if isinstance(t, VStructType):
            newt = t.get_field(self.member_name)
            if newt is not None:
                ac = newt.access_mod

                # Check if visible
                if ac == ACCESS_PRIVATE or ac == ACCESS_PRIVATE_MUT:
                    if t.module != scope.get_function().get_module():
                        raise TypeCheckError(self.report, f"field is not public", scope.get_function().name)

                return newt.xtype

        elif isinstance(t, VArray):
            if self.member_name == 'len':
                return module.add_type(VInt)

        elif isinstance(t, VModule):
            t = t.get_identifier(self.member_name)

            if isinstance(t, VStruct) or isinstance(t, VFunction):
                if t.get_module() != module:
                    if not t.pub:
                        raise TypeCheckError(self.report, f"member is not public", scope.get_function().name)
                return t.type
            else:
                return t

        elif isinstance(t, dict):
            return t[self.member_name].type

        else:
            raise TypeCheckError(self.expr.report, f"Type `{t}` does not have any members", scope.get_function().name)

        raise TypeCheckError(self.expr.report, f"Type `{t}` does not have any members", scope.get_function().name)

    def is_mut(self, module, scope):
        if not self.expr.is_mut(module, scope):
            return False

        t = self.expr.resolve_type(module, scope)

        if isinstance(t, VStructType):
            field = t.get_field(self.member_name)
            ac = field.access_mod

            # Never mut
            if ac == ACCESS_PRIVATE or ac == ACCESS_PUBLIC:
                return False

            # Only mut in same module
            elif ac == ACCESS_PRIVATE_MUT or ACCESS_PUBLIC_PROTECTED_MUT:
                return scope.get_function().get_module() == t.module

            # Always mut
            elif ac == ACCESS_PUBLIC_MUT:
                return True

        return False

    def __str__(self):
        return f'{self.expr}.{self.member_name}'


class ExprIndex(Expr):

    def __init__(self, src, at, report):
        """
        :type src: Expr
        :type at: Expr
        """
        super(ExprIndex, self).__init__(report)
        self.src = src
        self.at = at

    def resolve_type(self, module, scope):
        t = self.src.resolve_type(module, scope)
        at_type = self.at.resolve_type(module, scope)
        default_assertion(t, self.src.report, scope.get_function().name)
        default_assertion(at_type, self.at.report, scope.get_function().name)

        if isinstance(t, VArray):
            if not isinstance(at_type, VIntegerType):
                raise TypeCheckError(self.at.report, f"array index must be an integer type (got {at_type})", scope.get_function().name)
            return t.xtype

        elif isinstance(t, VMap):
            if at_type != t.key_type:
                raise TypeCheckError(self.at.report, f"map of type {t} expected key {t.key_type}, got {at_type}", scope.get_function().name)
            return t.value_type

        else:
            raise TypeCheckError(self.report, f"Index operator not supported for type {t}", scope.get_function().name)

    def is_mut(self, module, scope):
        return self.src.is_mut(module, scope)

    def __str__(self):
        return f'{self.src}[{self.at}]'


class ExprArrayLiteral(Expr):
    """
    Return a new initialized array of the given expressions
    """

    def __init__(self, exprs, report):
        """
        :type exprs: List[Expr]
        """
        super(ExprArrayLiteral, self).__init__(report)
        self.exprs = exprs

    def resolve_type(self, module, scope):
        xtype = None

        i = 0
        for expr in self.exprs:
            if xtype is None:
                xtype = expr.resolve_type(module, scope)
            else:
                xt = expr.resolve_type(module, scope)
                if xtype != xt:
                    raise TypeCheckError(expr.report, f"Array item at index `{i}` does not match type (expected `{xtype}`, got `{xt}`)", scope.get_function().name)
            i += 1

        default_assertion(xtype, expr.report, scope.get_function().name)

        return module.add_type(VArray(xtype))

    def is_mut(self, module, scope):
        return True

    def __str__(self):
        return "[" + ','.join([str(expr) for expr in self.exprs]) + "]"


class ExprArrayLiteralUninit(Expr):
    """
    Returns a new un-initialized (default initialized) array of the given type
    with the given amount of starting elements
    """

    def __init__(self, length, xtype, report):
        """
        :type length: Expr
        :type xtype: VType
        """
        super(ExprArrayLiteralUninit, self).__init__(report)
        self.length = length
        self.xtype = xtype

    def resolve_type(self, module, scope):
        self.xtype = module.resolve_type(self.xtype)
        default_assertion(self.xtype, self.report, scope.get_function().name)
        if not isinstance(self.length.resolve_type(module, scope), VIntegerType):
            raise TypeCheckError(self.length.report, "Length of array must be an integer", scope.get_function().name)
        return module.add_type(VArray(self.xtype))

    def is_mut(self, module, scope):
        return True

    def __str__(self):
        return f'[{self.length}]{self.xtype}'


class ExprUnary(Expr):

    def __init__(self, op, expr, report):
        """
        :type op: str
        :type expr: Expr
        """
        super(ExprUnary, self).__init__(report)
        self.op = op
        self.expr = expr

    def resolve_type(self, module, scope):
        t = self.expr.resolve_type(module, scope)
        if self.op == '!':
            if not isinstance(t, VBool):
                raise TypeCheckError(self.expr.report, f"unary op `{self.op}` only supports bool (got `{t}`)", scope.get_function().name)
        else:
            if not isinstance(t, VIntegerType):
                raise TypeCheckError(self.expr.report, f"unary op `{self.op}` only supports integer types (got `{t}`)", scope.get_function().name)
        return t

    def is_mut(self, module, scope):
        return True

    def __str__(self):
        return f'{self.op}{self.expr}'
