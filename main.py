from lark import *
from vast import *


if __name__ == '__main__':
    v_parser = Lark.open('v.lark')
    parse_tree = v_parser.parse(open('./test/test.v').read())  # type: Tree
    print(parse_tree.pretty())
