
#ifndef __MBASCII_H__
#define __MBASCII_H__

#include "vm.h"

#if 0

_VM_EXPORT_ vm_word_t mba_wr_reg(vm_word_t en, vm_word_t addr, vm_word_t reg,
	_VM_VA_CNT_ _VM_INPUT_ vm_word_t reg_value_count,
	_VM_VA_LST_ _VM_INPUT_ vm_word_t* val);

#else

vm_word_t mba_wr_reg(vm_word_t en, vm_word_t addr, vm_word_t reg,
	vm_word_t reg_value_count,
	vm_word_t* val);

#endif

#endif

