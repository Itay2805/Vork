from copy import copy
from typing import *


class VType:

    def __init__(self, mut):
        """
        :type mut: bool
        """
        self.mut = mut

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.mut == other.mut

    def copy(self):
        return copy(self)


class VVoidType(VType):
    
    def __init__(self):
        super(VVoidType, self).__init__(False)

    def __eq__(self, other):
        return False

    def __str__(self):
        return 'nothing'


class VUnresolvedType(VType):

    def __init__(self, mut, type_name):
        super(VUnresolvedType, self).__init__(mut)
        self.type_name = type_name

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.mut == other.mut and self.type_name == other.type_name

    def __str__(self):
        return f'{self.type_name}'


class VIntegerType(VType):
    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VIntegerType, self).__init__(mut)


#
# The builtin V types
#

class VI8(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VI8, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}i8'


class VI16(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VI16, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}i16'


class VInt(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VInt, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}int'


class VI64(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VI64, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}i64'


class VI128(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VI128, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}i128'


class VByte(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VByte, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}byte'


class VU16(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VU16, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}u16'


class VU32(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VU32, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}u32'


class VU64(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VU64, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}u64'


class VU128(VIntegerType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VU128, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}u128'

#
# Other types
#


class VBool(VType):

    def __init__(self, mut):
        """
        :type mut: bool
        """
        super(VBool, self).__init__(mut)

    def __str__(self):
        return f'{"mut " if self.mut else ""}bool'


class VArray(VType):

    def __init__(self, mut, type):
        """
        :type mut: bool
        :type type: VType
        """
        super(VArray, self).__init__(mut)
        self.type = type

    def __eq__(self, other):
        if isinstance(other, VArray) and self.mut == other.mut:
            return self.type == other.type
        return False

    def __str__(self):
        return f'{"mut " if self.mut else ""}[]{self.type}'


class VRef(VType):

    def __init__(self, mut, type):
        """
        :type mut: bool
        :type type: VType
        """
        super(VRef, self).__init__(mut)
        self.type = type

    def __eq__(self, other):
        if isinstance(other, VRef) and self.mut == other.mut:
            return self.type == other.type
        return False

    def __str__(self):
        return f'{"mut " if self.mut else ""}&{self.type}'


class VOptional(VType):

    def __init__(self, mut, type):
        """
        :type mut: bool
        :type type: VType
        """
        super(VOptional, self).__init__(mut)
        self.type = type

    def __eq__(self, other):
        if isinstance(other, VOptional) and self.mut == other.mut:
            return self.type == other.type
        return False

    def __str__(self):
        return f'{"mut " if self.mut else ""}?{self.type}'


class VMap(VType):

    def __init__(self, mut, type0, type1):
        """
        :type mut: bool
        :type type: VType
        """
        super(VMap, self).__init__(mut)
        self.type0 = type0
        self.type1 = type1

    def __eq__(self, other):
        if isinstance(other, VMap) and self.mut == other.mut:
            return self.type0 == other.type0 and self.type1 == other.type1
        return False

    def __str__(self):
        return f'{"mut " if self.mut else ""}map[{self.type0}]{self.type1}'


class VFunctionType(VType):

    def __init__(self, mut):
        super(VFunctionType, self).__init__(mut)
        self.param_types = []  # type: List[VType]
        self.return_types = []  # type: List[VType]

    def add_param(self, xtype):
        """
        :type type: VType
        """
        assert xtype is not None
        self.param_types.append(xtype)

    def __eq__(self, other):
        if isinstance(other, VFunctionType) and self.mut == other.mut:
            if self.return_types != other.return_types:
                return False
            if self.param_types != other.param_types:
                return False
            return True
        return False

    def __str__(self):
        # Format params
        params = ', '.join([str(param) for param in self.param_types])

        # Format return types
        return_types = ', '.join([f'{return_type}' for return_type in self.return_types])
        if len(self.return_types) > 1:
            return_types = f'({return_types})'

        return f'{"mut " if self.mut else ""}fn ({params}) {return_types}'


#
# Helpers
#

def is_integer(xtype):
    return isinstance(xtype, VIntegerType)


def is_bool(xtype):
    return isinstance(xtype, VBool)


def check_return_type(ret_type, xtype):
    """
    :type ret_type: VType
    :type xtype: VType
    :rtype: bool
    """

    # Check if types are the same
    if ret_type == xtype:
        return True

    # Check mut -> not mut
    xtype = xtype.copy()
    xtype.mut = False
    if ret_type == xtype:
        return True

    # Check if both are integer types
    # TODO: Only allow integers with lower bits to higher bits and same sign
    # TODO: Should probably make this cast the return expression or something
    if isinstance(ret_type, VIntegerType) and isinstance(xtype, VIntegerType):
        return True

    return False
