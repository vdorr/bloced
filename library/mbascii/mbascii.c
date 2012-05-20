
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

#define MBA_B_CHR(v) (hex_lut[((v)>>4)&15])
#define MBA_L_CHR(v) (hex_lut[(v)&15])

vm_word_t mba_wr_reg(vm_word_t en, vm_word_t addr, vm_word_t reg,
	vm_word_t reg_value_count, vm_word_t* values)
{
	if (!en)
	{
		return 0;
	}
	uint8_t buffer[16];
	const uint8_t function = 16;
	uint8_t lo;
	uint8_t hi;

	buffer[0] = ':';

	buffer[1] = MBA_B_CHR(addr);
	buffer[2] = MBA_L_CHR(addr);

	buffer[3] = MBA_B_CHR(function);
	buffer[4] = MBA_L_CHR(function);

	hi = MB_WORD_L(reg);
	lo = MB_WORD_H(reg);
	buffer[5] = MBA_B_CHR(hi);
	buffer[6] = MBA_L_CHR(hi);
	buffer[7] = MBA_B_CHR(lo);
	buffer[8] = MBA_L_CHR(lo);

	hi = MB_WORD_L(reg_value_count);
	lo = MB_WORD_H(reg_value_count);
	buffer[9] = MBA_B_CHR(hi);
	buffer[10] = MBA_L_CHR(hi);
	buffer[11] = MBA_B_CHR(lo);
	buffer[12] = MBA_L_CHR(lo);

	buffer[13] = MBA_B_CHR(reg_value_count << 1);
	buffer[14] = MBA_L_CHR(reg_value_count << 1);

	buffer[15] = 0;
	mba_send_string(buffer);
	uint8_t lrc = 0;
	int i;
	for (i = 0; i < reg_value_count; i++)
	{
		lrc = (uint8_t)((lrc + values[i]) & 0xff);
		lo = MB_WORD_H(values[i]);
		hi = MB_WORD_L(values[i]);
		buffer[0] = MBA_B_CHR(hi);
		buffer[1] = MBA_L_CHR(hi);
		buffer[2] = MBA_B_CHR(lo);
		buffer[3] = MBA_L_CHR(lo);
		buffer[4] = 0;
		mba_send_string(buffer);
	}
	buffer[0] = MBA_B_CHR(lrc);
	buffer[1] = MBA_L_CHR(lrc);
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


