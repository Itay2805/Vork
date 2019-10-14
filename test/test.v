module main

fn range(len int) []int {
    mut arr := [len]int
    for i := 0; i < len; i += 1 {
        arr[i] = i
    }
    return arr
}

import rand

fn gen_randoms(seed int) []int {
	mut randoms := [20]int
	rand.seed(seed)
	for i in range(20) {
		randoms[i] = rand.next(100)
	}
	return randoms
}

fn to_mut(a int) int {
    return a
}

fn main() {
    for i := 0; i < 10; i += 1 {
        if i == 5 {
            break
        }
        print(i)
    }
}
