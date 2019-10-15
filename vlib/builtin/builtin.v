module builtin

fn C.exit(code int)
pub fn exit(code int) {
    C.exit(code)
}
