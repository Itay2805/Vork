module builtin

fn C.print(a int)

pub fn print(a int) {
    C.print(a)
}
