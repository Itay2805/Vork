from vworkspace import VWorkspace
from vinterpreter import VInterpreter
from vparser import VParser

import argparse

if __name__ == '__main__':
    if False:
        print(VParser.parse(open('./test/test.v').read()).pretty())
    else:
        # TODO: Proper shit
        workspace = VWorkspace(['./test'])
        module = workspace.load_module('main')
        if module is not None:
            workspace.type_check()

            interpreter = VInterpreter(module)
            interpreter.eval_function('main')
