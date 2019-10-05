from vlexer import VLexer
from vparser import VParser
from vast import VModule
from vinterpreter import VInterpreter
import dumper

if __name__ == '__main__':
    lexer = VLexer()
    parser = VParser()

    tokens = lexer.tokenize("""
fn add(a, b int) (int) {
    return a + b
}
""")

    module = parser.parse(tokens)  # type: VModule
    module.type_checking()

    interp = VInterpreter(module)
    print(interp.run_function('add', [5, 3]))

    # dumper.default_dumper.instance_dump = ['vast', 'vtypes', 'vstmt', 'vexpr']
    # dumper.dump(module)

