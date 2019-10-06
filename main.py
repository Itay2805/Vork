from vlexer import VLexer
from vparser import VParser
from vast import VModule
from vinterpreter import VInterpreter
import dumper

if __name__ == '__main__':
    lexer = VLexer()
    parser = VParser()

    tokens = lexer.tokenize("""
fn sub(a, b int) (int) {
    if a < b {
        assert false
    } else if a == b {
        return 1000
    } else {
        return a - b
    }
    
    // dummy because type checking
    return 0
}
""")

    module = parser.parse(tokens)  # type: VModule
    module.type_checking()

    interp = VInterpreter(module)
    print(interp.run_function('sub', [3, 3]))

    dumper.default_dumper.instance_dump = ['vast', 'vtypes', 'vstmt', 'vexpr']
    dumper.dump(module)

