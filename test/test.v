module main

const Pi = 3

const (
    A = B
    B = 3
)

fn range(len int) []int {
    mut arr := [len]int
    for i := 0; i < len; i += 1 {
        arr[i] = i
    }
    return arr
}

fn main() {
    a := [A,B]
    for i in a {
        print(i)
    }
}
