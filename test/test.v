module main

struct Test {
mut:
    a int
}

fn test() Test {
    return Test{3}
}

fn main() {
    a := false
    assert !a
}
