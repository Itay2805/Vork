fn C.test() ?int

fn test() int {
    return C.test() or { return 0 }
}
