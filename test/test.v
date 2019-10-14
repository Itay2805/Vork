module main

struct Test {
mut:
    a int
}

fn test() Test {
    return Test{3}
}

fn main() {
    for i := 0; i < 10; i += 1 {
        print(i)
    }
}
