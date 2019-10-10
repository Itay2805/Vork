module main

fn do_something(a, b int) int {
    if a > 10 {
        return 0
    } else if(b > 10) {
        return 1
    } else {
        return 2
    }
    return 0
}

fn main() {
    c := do_something(5, 5)
    print(c)
}
