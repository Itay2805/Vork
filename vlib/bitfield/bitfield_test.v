import bitfield

fn test_bf_new_size() {
	instance := bitfield.new(75)
	assert instance.getsize() == 75
}

fn test_bf_set_clear_toggle_get() {
	mut instance := bitfield.new(75)
	instance.setbit(47)
	assert instance.getbit(47) == 1
	instance.clearbit(47)
	assert instance.getbit(47) == 0
	instance.togglebit(47)
	assert instance.getbit(47) == 1
}

