module bitfield

struct BitField {
mut:
    size int
    field []u32
}

const (
    SLOT_SIZE = 32
)

fn bitmask(bitnr int) u32 {
	return u32(u32(1) << u32(bitnr % SLOT_SIZE))
}

fn bitslot(size int) int {
	return size / SLOT_SIZE
}

fn bitget(instance BitField, bitnr int) int {
	return int(instance.field[bitslot(bitnr)] >> u32(bitnr % SLOT_SIZE)) & 1
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

fn min(input1 int, input2 int) int {
	if input1 < input2 {
		return input1
	}
	else {
		return input2
	}

	return 0
}

fn bitnslots(length int) int {
	return (length - 1) / SLOT_SIZE + 1
}

fn cleartail(instance mut BitField) {
	tail := instance.size % SLOT_SIZE
	if tail != 0 {
		mask := u32((1 << tail) - 1)
		instance.field[bitnslots(instance.size) - 1] = instance.field[bitnslots(instance.size) - 1] & mask
	}
}

pub fn new(size int) BitField {
    output := BitField {
        size: size
        field: [bitnslots(size)]u32
    }
    return output
}

pub fn (instance BitField) getbit(bitnr int) int {
	if bitnr >= instance.size {return 0}
    bit := bitget(instance, bitnr)
	return bit
}

pub fn (instance mut BitField) setbit(bitnr int) {
	if bitnr >= instance.size {return}
	bitset(mut instance, bitnr)
}

pub fn (instance mut BitField) clearbit(bitnr int) {
	if bitnr >= instance.size {return}
	bitclear(mut instance, bitnr)
}

pub fn (instance mut BitField) setall() {
	for i := 0; i < bitnslots(instance.size); i++ {
		instance.field[i] = u32(-1)
	}
	cleartail(mut instance)
}

pub fn (instance mut BitField) clearall() {
	for i := 0; i < bitnslots(instance.size); i++ {
		instance.field[i] = u32(0)
	}
}

pub fn (instance mut BitField) togglebit(bitnr int) {
	if bitnr >= instance.size {return}
	bittoggle(mut instance, bitnr)
}

pub fn (instance BitField) getsize() int {
	return instance.size
}
