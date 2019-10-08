from vlexer import VLexer
from vparser import VParser
from vast import VModule
from vinterpreter import VInterpreter
import dumper

if __name__ == '__main__':
    lexer = VLexer()
    parser = VParser()

    tokens = lexer.tokenize("""
fn get_power(a int) int {
    return a * a
}

fn do_it() int {
    return get_power(2) / 2
}
""")

    module = parser.parse(tokens)  # type: VModule
    module.type_checking()

    dumper.default_dumper.instance_dump = ['vast', 'vtypes', 'vstmt', 'vexpr']
    dumper.dump(module)

    interp = VInterpreter(module)
    print(interp.eval_function('do_it', []))


