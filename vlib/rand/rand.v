module rand

fn C.rand() int
fn C.srand(s int)

pub fn seed(s int) {
    C.srand(s)
}

pub fn next(max int) int {
    return C.rand() % max
}

