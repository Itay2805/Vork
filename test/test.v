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
	mut randoms1 := gen_randoms(42)
	mut randoms2 := gen_randoms(42)
	assert randoms1.len == randoms2.len

	mut len := to_mut(randoms1.len)
	for i in range(len) {
		assert randoms1[i] == randoms2[i]
	}

	randoms1 = gen_randoms(256)
	randoms2 = gen_randoms(256)
	assert randoms1.len == randoms2.len

	len = to_mut(randoms1.len)
	for i in range(len) {
		assert randoms1[i] == randoms2[i]
	}
}
