
_VM_EXPORT_ vm_word_t d_in(vm_word_t nr); /* simple digital input */
_VM_EXPORT_ void d_out(vm_word_t nr, vm_word_t v); // simple digital output
_VM_EXPORT_ vm_word_t a_in(vm_word_t nr, vm_word_t a_ref);
_VM_EXPORT_ void a_out(vm_word_t nr, vm_word_t dc);

_VM_EXPORT_ vm_dword_t time_ms();
_VM_EXPORT_ vm_dword_t time_us();

_VM_EXPORT_ void dummy(vm_word_t nr, vm_word_t a_ref, vm_word_t *x, vm_word_t * y);

