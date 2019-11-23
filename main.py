from vork.tokenizer import *
from vork.parser import *

BOLD = '\033[01m'
RESET = '\033[0m'
GREEN = '\033[32m'
RED = '\033[31m'


def parse_file(filename):
    with open(filename, 'r') as f:
        text = f.read()
        lines = text.splitlines()
        tokenizer = Tokenizer(text)
        parser = Parser(tokenizer)
        try:
            return parser.parse()
        except Exception as e:
            # TODO: error recovering?
            # import traceback
            # traceback.print_exc()

            pos = tokenizer.token.pos

            msg = ", ".join(e.args)
            if msg == '':
                msg = 'Unexpected token'

            print(f'{BOLD}{filename}:{pos.start_line + 1}:{pos.start_column + 1}:{RESET} {RED}{BOLD}syntax error:{RESET} {msg}')

            line = lines[pos.start_line]
            line = line[:pos.start_column] + BOLD + line[pos.start_column:pos.end_column] + RESET + line[pos.end_column:]
            print(line)

            c = ''
            for i in range(pos.start_column):
                if lines[pos.start_line][i] == '\t':
                    c += '\t'
                else:
                    c += ' '

            print(c + BOLD + RED + '^' + '~' * (pos.end_column - pos.start_column - 1) + RESET)
            print()

            return None


def main():
    res = parse_file("test.v")
    if res is None:
        exit(-1)

    module = Module()

    for r in res:
        if isinstance(r, ModuleDecl):
            module.name = r.name
        else:
            module.add(r)

    module.type_checking()

    print('\n'.join(map(str, res)))


if __name__ == '__main__':
    main()
