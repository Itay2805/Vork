module bitfield

/*
bitfield is a module for
manipulating arrays of bits, i.e. series of zeroes and ones spread across an
array of storage units (unsigned 32-bit integers).
BitField structure
------------------
Bit arrays are stored in data structures called 'BitField'. The structure is
'opaque', i.e. its internals are not available to the end user. This module
provides API (functions and methods) for accessing and modifying bit arrays.
*/

pub struct BitField {
mut:
	size int
	//field *u32
	field []u32
}

// helper functions
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
	return (instance.field[bitslot(bitnr)] >> (bitnr % SLOT_SIZE)) & u32(1)
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
}

fn bitnslots(length int) int {
	return (length - 1) / SLOT_SIZE + 1
}

fn cleartail(instance mut BitField) {
	tail := instance.size % SLOT_SIZE
	if tail != 0 {
		// create a mask for the tail
		mask := u32((1 << tail) - 1)
		// clear the extra bits
		instance.field[bitnslots(instance.size) - 1] = instance.field[bitnslots(instance.size) - 1] & mask
	}
}

// public functions

// from_bytes() converts a byte array into a bitfield.
pub fn from_bytes(input []byte) BitField {
	mut output := new(input.len * 8)
	for i, b in input {
		output.field[i / 4] |= u32(b) << ((i % 4) * 8)
	}
	return output
}