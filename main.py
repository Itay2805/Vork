from vlexer import VLexer
from vparser import VParser
from vast import ModuleDecl
import dumper

if __name__ == '__main__':
    lexer = VLexer()
    parser = VParser()

    tokens = lexer.tokenize("""
fn test(a, b type_b) (type_a) {
}

type type_a type_b
type type_b int
""")

    module = parser.parse(tokens)  # type: ModuleDecl
    module.resolve_types()

    dumper.default_dumper.instance_dump = ['vast', 'vtypes', 'vstmt', 'vexpr']
    dumper.dump(module)

