from vlexer import VLexer
from vparser import VParser
from vast import ModuleDecl
import dumper

if __name__ == '__main__':
    lexer = VLexer()
    parser = VParser()

    tokens = lexer.tokenize("""
fn test() (?int, ?int) {
    assert 123
}
""")

    module = parser.parse(tokens)  # type: ModuleDecl
    module.resolve_types()

    dumper.default_dumper.instance_dump = ['vast', 'vtypes', 'vstmt', 'vexpr']
    dumper.dump(module)
