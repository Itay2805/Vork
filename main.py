from vworkspace import VWorkspace
from vinterpreter import VInterpreter

if __name__ == '__main__':
    workspace = VWorkspace(['./test'])
    module = workspace.load_module('main')
    workspace.type_check()
    interpreter = VInterpreter(module)
    interpreter.eval_function('main', [])
