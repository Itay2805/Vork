module main

fn test(arr []i8) {
    print(arr.len)
}

fn main() {
    mut arr := [i8(1),2,3,4]
    test(arr)
    print(arr[0])
}
