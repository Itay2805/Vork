from vlexer import VLexer
from vparser import VParser
import dumper

if __name__ == '__main__':
    lexer = VLexer()
    parser = VParser()

    tokens = lexer.tokenize("""
fn test() {
    {
        assert false
    }
    assert false
}
""")

    module = parser.parse(tokens)

    dumper.default_dumper.instance_dump = ['vast', 'vtypes', 'vstmt', 'vexpr']
    dumper.dump(module)
