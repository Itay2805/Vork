module main

import bitfield

fn main() {
    mut instance := bitfield.new(75)
    bitfield.bitset(mut instance, 47)
    assert bitfield.bitget(instance, 47) == 1
    bitfield.bitclear(mut instance, 47)
    assert bitfield.bitget(instance, 47) == 0
    bitfield.bittoggle(mut instance, 47)
    assert bitfield.bitget(instance, 47) == 1
}
