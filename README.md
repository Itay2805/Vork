# Vork

Vork will eventually be a fully fledged V implementation, including 
parser, compiler and interpreter (and maybe more will see how much time 
I will have)

Right now it is only the parser and interpreter, once I get the 
interpreter to have all/most of V's features I will move on to work on 
a compiler.

## vlib
The vlib shipped with the compiler is mostly copied from the official 
vlib. main differences are that most of the implementation of the 
builtins moved to be part of the code gen.

for example while the official vlib has alot of the array functions be 
implemented in V, and the compiler will turn say `[1,2,3,4]` to a 
`new_array_from_c_array`, we don't do that, and leave the creation of 
the array to the implementation of the code gen.

this allows to easily have the interpreter without starting to have 
different builtin implementations in v itself (for example, currently 
the js code gen of v has different v builtin implementation)

## Implemented
currently the program will generate a first AST using Earley parser 
(V is too ambiguous for a LALR). Then it will transform the Tree into
bytecode like AST; which then we can either run directly in the 
interpreter or later on maybe do code gen with it.

* All binary and unary expressions (postfix and prefix operators are missing currently)
* Integers, Boolean and Float types
* Arrays (can technically parse Ref and Opt but does not actually handle them)
* Functions and function calling
* Modules and imports  
* Structs and access modifiers
* Methods
* asserts
* if\else\if else and most of the for loops
* variable declaration and assignment (and op assignment `+=`) with mutability checking
* consts
* Interop functions (the interpreter handles what to do for each interop function)

## TODO
kinda in the order I wanna work on stuff and kinda not

* ranged for loops (0..x)
* enums
* optionals
* strings
* maps
* go statement
* match
* expression if
* references/pointers/whatever
* figure postfix and prefix ++/--
* interfaces
* attributes
* fix embedded structs
* operator overloading
* generics
* compile time if