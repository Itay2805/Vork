from vork.tokenizer import *
from vork.parser import *


def main():
    workspace = Workspace([])
    workspace.load_main('./')
    print(workspace.load_module('main'))


if __name__ == '__main__':
    main()
