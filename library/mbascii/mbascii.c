
//#include "vm.h"//TODO

#include "Arduino.h"
#include "mbascii.h"

int mba_send(unsigned char* buffer, int max_send)
{
	//Serial.print(buffer);//probably need extern "C" wrap
	return 0;
}

vm_word_t mba_wr_reg(vm_word_t address, vm_word_t reg)
{
/*int count = 666;
va_list ap;
va_start (ap, count);
for (i = 0; i < count; i++)
{
	va_arg (ap, int);
}
va_end (ap); */
	return 0;
}

vm_word_t mba_wr_coil()
{
	return 0;
}


