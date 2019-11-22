# Vork

Vork will eventually be a fully fledged V implementation.

Right now it is just a parser, once I get a full parser then I will start working on code gen.

## Example
for now all that it does is read in a file and try to parse it. Right now there is no error
recovery on a syntax error, but there is a nice printout so you can hopefully understand what went wrong.

The parse output will be printed and is formated in a lisp like way

```v
fn fib(n int) int {
        if n <= 1 {
                return n
        }
        return fib(n - 1) + fib(n - 2)
}

fn main() {
        i := 0
        for i = 0; i < 10; ++i {
                println(fib(i))
        }
}
```

```lisp
(func fib ((n int)) int
  (block
    (if (<= n 1)
      (block
        (return n)))
    (return (+ (call fib ((- n 1))) (call fib ((- n 2)))))))
(func main () 
  (block
    (var (i) 0)
    (for (= i 0) (< i 10) (prefix ++ i)
      (block
        (call println ((call fib (i))))))))
```

## Formal grammar
The [lark](v.lark) file has an old formal grammar I defined which I am going to keep as a reference, maybe after finishing the hand written parser I will go back and rewrite the formal grammar to be updated.

hopefully by the done I am finished with the parser the (official) formal grammar will be out already :shrug:

## Implemented
* All binary and unary expressions
    * post fix operators are not added to the ast yet
    * Function calls can not take `mut` modifier to expression for now
* Almost full type parsing support
    * missing function types
* Functions, methods and interop functions
    * missing generics
* Module and Imports
* Structs with their access modifiers
    * missing the base type
    * missing generics
* asserts
* if\if else\else
* Most of the for loops
    * in c like for loops can not declare a variable at the start...
    * missing for with only condition (`for true`)
    * missing ranged for loop
* Constants
* Variable declarations
* Enums declarations 
* Integer and Float literals

## Missing
* String, map and array literals
* interfaces
* match
* go statement
* or statement (is it still a thing?)
* Attributes
* compile time if

## Problems
Right now the parser ignores new lines **completely**, that is because from what I could see the official V compiler also does that, but in an inconsistent way... sometimes it ignores it and sometimes not...

for the most part it is not actually a problem, but specifically for the `*` operator it makes a problem, because it is used both for deref and for multipication
```v
a := 123
b := &a
*b = 456
```
will not give the correct output! 

the simplest way to get around it for now is to simply seround it with a block
```v
a := 123
b := &a
{*b = 456}
```

but the real solution is to wait for a formal grammar and see how newlines should actually be handled.

note that this problem happens on any operator which may be used in both unary and binary way, including `-` and alike...