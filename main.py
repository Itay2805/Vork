from vworkspace import VWorkspace
from vinterpreter import VInterpreter
from vparser import VParser
from vast import VModule

import sys

import argparse

if __name__ == '__main__':
    if False:
        print(VParser.parse(open('./test/test.v').read()).pretty())
    else:
        # TODO: Proper shit
        workspace = VWorkspace(['./test'])
        module = workspace.load_module('main')
        if module is not None and isinstance(module, VModule):
            if workspace.type_check():
                interpreter = VInterpreter(module)
                interpreter.eval_function('main')
            else:
                sys.exit(2)
        else:
            sys.exit(1)