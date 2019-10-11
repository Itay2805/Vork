module main

struct my_optional_int {
    is_valid bool
    number int
}

fn unwrap_my_optional_int(opt my_optional_int, default int) int {
    if my_optional_int.is_valid {
        return my_optional_int.number
    }
    return default
}

fn main() {
    opt := my_optional_int{false, 0}
    c := unwrap_my_optional_int(opt, -1)
    print(c)
}
