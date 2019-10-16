import rand

fn gen_randoms(seed int) []int {
	mut randoms := [20]int
	rand.seed(seed)
	for i := 0; i < 20; i += 1 {
		randoms[i] = rand.next(100)
	}
	return randoms
}

fn test_rand_reproducibility() {
	mut randoms1 := gen_randoms(42)
	mut randoms2 := gen_randoms(42)
	assert randoms1.len == randoms2.len

	mut len := randoms1.len
	for i := 0; i < len; i += 1 {
		assert randoms1[i] == randoms2[i]
	}

	randoms1 = gen_randoms(256)
	randoms2 = gen_randoms(256)
	assert randoms1.len == randoms2.len

	len = randoms1.len
	for i := 0; i < len; i += 1 {
		assert randoms1[i] == randoms2[i]
	}
}
