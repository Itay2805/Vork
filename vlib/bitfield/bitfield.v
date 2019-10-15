module bitfield

struct BitField {
mut:
    size int
    field []u32
}

const (
    SLOT_SIZE = 32
)

fn bitslot(size int) int {
	return size / SLOT_SIZE
}

fn bitget(instance BitField, bitnr int) int {
	return int(instance.field[bitslot(bitnr)] >> u32(bitnr % SLOT_SIZE)) & 1
}

fn bitnslots(length int) int {
	return (length - 1) / SLOT_SIZE + 1
}

pub fn new(size int) BitField {
    output := BitField {
        size: size
        field: [bitnslots(size)]u32
    }
    return output
}

pub fn (instance BitField) getbit(bitnr int) int {
	if bitnr >= instance.size {
	    return 0
    }
	return bitget(instance, bitnr)
}
