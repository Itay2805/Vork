module bitfield

struct BitField {
mut:
	size int
	field []u32
}

fn bitmask(bitnr int) u32 {
	return u32(u32(1) << u32(bitnr % 32))
}

fn bitslot(size int) int {
	return size / 32
}

fn bitget(instance BitField, bitnr int) int {
	return int(instance.field[bitslot(bitnr)] >> u32(bitnr % 32)) & 1
}

fn bitset(instance mut BitField, bitnr int) {
	instance.field[bitslot(bitnr)] = instance.field[bitslot(bitnr)] | bitmask(bitnr)
}

fn bitclear(instance mut BitField, bitnr int) {
	instance.field[bitslot(bitnr)] = instance.field[bitslot(bitnr)] & ~bitmask(bitnr)
}

fn bittoggle(instance mut BitField, bitnr int) {
	instance.field[bitslot(bitnr)] = instance.field[bitslot(bitnr)] ^ bitmask(bitnr)
}

fn bitnslots(length int) int {
	return (length - 1) / 32 + 1
}

fn new(size int) BitField {
    output := BitField {
        size: size
        field: [bitnslots(size)]u32
    }
    return output
}
