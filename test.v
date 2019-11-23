fn C.printint(num int)

fn main() {
	for _ in 0..5 {
		C.printint(_)
	}
	C.printint(123)
}