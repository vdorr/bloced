
#ifndef __I2C_EXPORT_H__
#define __I2C_EXPORT_H__

#include "vm.h"

#if 0

_VM_EXPORT_ void i2c_init(vm_word_t ch, vm_word_t addr, vm_word_t speed, vm_word_t* st);

_VM_EXPORT_ void i2c_wr(vm_word_t en, vm_word_t addr,
	_VM_VA_CNT_ _VM_INPUT_ vm_word_t bytes_in_count,
	_VM_VA_LST_ _VM_INPUT_ vm_word_t* bytes,
	vm_word_t* st);

_VM_EXPORT_ void i2c_rd(vm_word_t en, vm_word_t addr,
	_VM_VA_CNT_ _VM_OUTPUT_ vm_word_t bytes_out_count,
	_VM_VA_LST_ _VM_OUTPUT_ vm_word_t* bytes,
	vm_word_t* st);

#else


#endif

#endif

