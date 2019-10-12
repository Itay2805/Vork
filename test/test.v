module main

struct my_optional_int {
    is_valid bool
    number int
}

fn unwrap_my_optional_int(opt my_optional_int, default int) int {
    if opt.is_valid {
        return opt.number
    }
    return default
}

fn main() {
    mut opt := my_optional_int{true, 100}
    c := unwrap_my_optional_int(opt, 0)
    opt.is_valid = false
    print(c)
}
