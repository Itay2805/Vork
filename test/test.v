module main

fn modify_my_array(arr mut []int) []int {
    for i, item in arr {
        arr[i] = item + 1
    }
    return arr
}

fn main() {
    for item in modify_my_array(mut [1,2,3]) {
        print(item)
    }
}
