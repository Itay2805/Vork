from copy import copy
from typing import *


class VType:

    def __init__(self):
        self.module = None  # type: VModule

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def copy(self):
        return copy(self)


class VVoidType(VType):

    def __eq__(self, other):
        return False

    def __str__(self):
        return 'nothing'


class VUnresolvedType(VType):

    def __init__(self, module, type_name):
        super(VUnresolvedType, self).__init__()
        self.type_name = type_name

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.type_name == other.type_name

    def __str__(self):
        return f'{self.type_name}'


class VIntegerType(VType):

    def __init__(self, bits, sign):
        super(VIntegerType, self).__init__()
        self.bits = bits
        self.sign = sign

    def __eq__(self, other):
        if isinstance(other, VIntegerType):
            return self.bits == other.bits and self.sign == other.sign
        return False

    def __str__(self):
        return f"{'i' if self.sign else 'u'}{self.bits}"


VInt = VIntegerType(32, True)

#
# Other types
#


class VBool(VType):

    def __str__(self):
        return f'bool'


class VArray(VType):

    def __init__(self, xtype):
        """
        :type xtype: VType
        """
        super(VArray, self).__init__()
        self.xtype = xtype

    def __eq__(self, other):
        if isinstance(other, VArray):
            return self.xtype == other.xtype
        return False

    def __str__(self):
        return f'[]{self.xtype}'


class VRef(VType):

    def __init__(self, type):
        """
        :type type: VType
        """
        super(VRef, self).__init__()
        self.type = type

    def __eq__(self, other):
        if isinstance(other, VRef):
            return self.type == other.type
        return False

    def __str__(self):
        return f'&{self.type}'


class VOptional(VType):

    def __init__(self, xtype):
        """
        :type xtype: VType
        """
        super(VOptional, self).__init__()
        self.xtype = xtype

    def __eq__(self, other):
        if isinstance(other, VOptional):
            return self.xtype == other.xtype
        return False

    def __str__(self):
        return f'?{self.xtype}'


class VMap(VType):

    def __init__(self, key, value):
        """
        :type key: VType
        :type value: VType
        """
        super(VMap, self).__init__()
        self.key_type = key
        self.value_type = value

    def __eq__(self, other):
        if isinstance(other, VMap):
            return self.key_type == other.key_type and self.value_type == other.value_type
        return False

    def __str__(self):
        return f'map[{self.key_type}]{self.value_type}'


class VFunctionType(VType):

    def __init__(self):
        super(VFunctionType, self).__init__()
        self.param_types = []  # type: List[Tuple[VType, bool]]
        self.return_types = []  # type: List[VType]

    def add_param(self, mut, xtype):
        """
        :type mut: bool
        :type type: VType
        """
        self.param_types.append((xtype, mut))

    def add_return_type(self, xtype):
        """
        :type mut: bool
        :type type: VType
        """
        self.return_types.append(xtype)

    def __eq__(self, other):
        if isinstance(other, VFunctionType):
            if self.return_types != other.return_types:
                return False
            if self.param_types != other.param_types:
                return False
            return True
        return False

    def __str__(self):
        # Format params
        params = ', '.join(['mut ' if param[1] else '' + str(param[0]) for param in self.param_types])

        # Format return types
        return_types = ', '.join(map(str, self.return_types))
        if len(self.return_types) > 1:
            return_types = f'({return_types})'

        return f'fn ({params}) {return_types}'


ACCESS_PRIVATE = 'private'
ACCESS_PRIVATE_MUT = 'mut'
ACCESS_PUBLIC = 'pub'
ACCESS_PUBLIC_PROTECTED_MUT = 'pub mut'
ACCESS_PUBLIC_MUT = 'pub mut mut'


class VStructField:

    def __init__(self, name, access_mod, xtype):
        """

        :type name: str
        :type access_mod: str
        :type xtype: VTYpe
        """
        self.name = name
        self.access_mod = access_mod
        self.xtype = xtype


class VStructType(VType):

    def __init__(self, embedded, fields):
        """
        :type name: str
        :type embedded: VStructType
        :type fields: List[VStructField]
        """
        super(VStructType, self).__init__()
        self.embedded = embedded
        self.fields = fields

    def get_field(self, name):
        # Check in our fields
        for field in self.fields:
            if field.name == name:
                return field

        # Check embedded type
        if self.embedded is not None:
            return self.embedded.get_field(name)

        return None

    def __eq__(self, other):
        if isinstance(other, VStructType):
            if self.embedded != other.embedded:
                return False
            if self.fields != other.fields:
                return False
            return True
        return False

    def __str__(self):
        s = f'struct '
        s += '{\n'

        if self.embedded is not None:
            s += f'\t{self.embedded}\n'

        last_ac = None
        for field in self.fields:

            if last_ac != field.access_mod:
                last_ac = field.access_mod
                s += f'{last_ac}:\n'

            s += f'\t{field.name} {field.xtype}\n'

        s += '}'
        return s


#
# Helpers
#

def is_integer(xtype):
    return isinstance(xtype, VIntegerType)


def is_bool(xtype):
    return isinstance(xtype, VBool)


def default_value_for_type(xtype):
    from vexpr import ExprBoolLiteral, ExprIntegerLiteral, ExprStructLiteral

    default = {
        VBool: ExprBoolLiteral(False),
        VStructType: ExprStructLiteral(False, xtype, [])
    }

    # Special case to handle all integers
    if isinstance(xtype, VIntegerType):
        return ExprIntegerLiteral(0)

    return default[xtype.__class__]
