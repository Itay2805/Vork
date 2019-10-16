from vinterpreter import VInterpreter
from vworkspace import VWorkspace
from vparser import VParser, TypeCheckError
from vast import VModule
from colors import *

import sys

import argparse

if __name__ == '__main__':
    test = True

    # TODO: Proper shit
    workspace = VWorkspace(['./test'], load_module_tests=test)
    module = workspace.load_module('main')
    if module is not None and isinstance(module, VModule):
        if workspace.type_check():
            interpreter = VInterpreter(module)

            # Running tests
            if test:

                # Find all teh functions to run
                functions = []
                for name in module.identifiers:
                    if name.startswith('test_'):
                        functions.append(name)

                print('running the following tests:')
                for fun in functions:
                    print(f'\t* {fun}')

                final_errors = []

                print()

                # Run them
                for func in functions:
                    try:
                        interpreter.eval_function(func)
                        print(f'{GREEN}.{RESET}', end='')
                    except TypeCheckError as e:
                        print(f'{RED}F{RESET}', end='')
                        final_errors.append(e)
                    except AssertionError as e:
                        print(f'{RED}E{RESET}', end='')
                        # TODO

                print()
                print()

                # Print the errors
                print(f'results: {len(functions) - len(final_errors)}/{len(functions)} passed')
                for err in final_errors:
                    err.report(f'{BOLD}{RED}assertion{RESET}', err.msg, err.func)

                sys.exit(len(final_errors))

            # just run main
            else:
                interpreter.eval_function('main')
        else:
            sys.exit(2)
    else:
        sys.exit(1)