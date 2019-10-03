#!/usr/bin/python
from vlexer import VLexer
from vparser import VParser


if __name__ == '__main__':
    lexer = VLexer()
    parser = VParser()
    text = """
struct User {
	age int
} 

fn main(a int) {
    color := Color.red
    println(color)
}
"""
    lex = lexer.tokenize(text)
    # for t in lex:
    #     print(t)
    tree = parser.parse(lex)
    print(tree)
