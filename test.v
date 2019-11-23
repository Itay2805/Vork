module test

enum Color {
    red green blue
}

fn main(arr []int) {
    assert Color.red == Color.green
}
