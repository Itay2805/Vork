module main

fn range(len int) []int {
    mut arr := [len]int
    for i := 0; i < len; i = i + 1 {
        arr[i] = i
    }
    return arr
}

fn main() {
    for item in range(6) {
        print(item)
    }
}
