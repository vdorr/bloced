
//#include "vm.h"//TODO

#include "Arduino.h"
#include "mbascii.h"

#if 0 //TODO big endian target
#define MACHINE_TO_MB_WORD()
#else
#define MB_WORD_L(x) (((x)&0xff00)>>8)
#define MB_WORD_H(x) ((x)&0xff)
#endif

const char* hex_lut = "0123456789abcdef";

extern int mba_send_string(const uint8_t* buffer);

vm_word_t mba_wr_reg(vm_word_t en, vm_word_t addr, vm_word_t reg,
	vm_word_t reg_value_count, vm_word_t* values)
{
	if (!en)
	{
		return 0;
	}
	uint8_t buffer[6];
	const uint8_t function = 16;
	buffer[0] = ':';
	buffer[1] = hex_lut[(addr >> 4) & 15];
	buffer[2] = hex_lut[addr & 15];
	buffer[3] = hex_lut[(function >> 4) & 15];
	buffer[4] = hex_lut[function & 15];
	buffer[5] = 0;
	mba_send_string(buffer);
	uint8_t lrc = 0;
	int i;
	for (i = 0; i < reg_value_count; i++)
	{
		lrc = (uint8_t)((lrc + values[i]) & 0xff);
		uint8_t l = MB_WORD_H(values[i]);
		uint8_t h = MB_WORD_L(values[i]);
		buffer[0] = hex_lut[h >> 4];
		buffer[1] = hex_lut[h & 15];
		buffer[2] = hex_lut[l >> 4];
		buffer[3] = hex_lut[h & 15];
		buffer[4] = 0;
		mba_send_string(buffer);
	}
	buffer[0] = hex_lut[lrc >> 4];
	buffer[1] = hex_lut[lrc & 15];
	buffer[2] = '\r';
	buffer[3] = '\n';
	buffer[4] = 0;
	mba_send_string(buffer);
	return 1;
}

vm_word_t mba_wr_coil()
{
	return 0;
}


