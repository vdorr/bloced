
#if defined(TEST01)

#include "../../target/arduino/include/vm.h"

#else

#include "Arduino.h"
#include "mbascii.h"

#endif

#if 0 //TODO big endian target
#define MACHINE_TO_MB_WORD()
#else
#define MB_WORD_L(x) (((x)&0xff00)>>8)
#define MB_WORD_H(x) ((x)&0xff)
#endif

const char* hex_lut = "0123456789ABCDEF";

#if defined(TEST01)

#include <stdio.h>

void mba_send_string(const uint8_t* buffer)
{
	printf("%s:%i '%s'\n", __FUNCTION__, __LINE__, buffer);
}

#else
extern int mba_send_string(const uint8_t* buffer);
#endif

#define MBA_B_CHR(v) (hex_lut[((v)>>4)&15])
#define MBA_L_CHR(v) (hex_lut[(v)&15])
#define MBA_LRC_UPD(lrc, v) ((lrc)+(v))
/*#define MBA_LRC_UPD(lrc, v) ((uint8_t)(((uint8_t)(lrc)+(v))&0xff))*/

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
	uint8_t lrc = 0;

	buffer[0] = ':';

	buffer[1] = MBA_B_CHR(addr);
	buffer[2] = MBA_L_CHR(addr);
	lrc = MBA_LRC_UPD(lrc, addr);

	buffer[3] = MBA_B_CHR(function);
	buffer[4] = MBA_L_CHR(function);
	lrc = MBA_LRC_UPD(lrc, function);

	hi = MB_WORD_L(reg);
	lo = MB_WORD_H(reg);
	buffer[5] = MBA_B_CHR(hi);
	buffer[6] = MBA_L_CHR(hi);
	buffer[7] = MBA_B_CHR(lo);
	buffer[8] = MBA_L_CHR(lo);
	lrc = MBA_LRC_UPD(lrc, hi);
	lrc = MBA_LRC_UPD(lrc, lo);

	hi = MB_WORD_L(reg_value_count);
	lo = MB_WORD_H(reg_value_count);
	buffer[9] = MBA_B_CHR(hi);
	buffer[10] = MBA_L_CHR(hi);
	buffer[11] = MBA_B_CHR(lo);
	buffer[12] = MBA_L_CHR(lo);
	lrc = MBA_LRC_UPD(lrc, hi);
	lrc = MBA_LRC_UPD(lrc, lo);

	buffer[13] = MBA_B_CHR(reg_value_count << 1);
	buffer[14] = MBA_L_CHR(reg_value_count << 1);
	lrc = MBA_LRC_UPD(lrc, reg_value_count << 1);

	buffer[15] = 0;
	mba_send_string(buffer);

	int i;
	for (i = 0; i < reg_value_count; i++)
	{
		lo = MB_WORD_H(values[i]);
		hi = MB_WORD_L(values[i]);
		lrc = MBA_LRC_UPD(lrc, hi);
		lrc = MBA_LRC_UPD(lrc, lo);
		buffer[0] = MBA_B_CHR(hi);
		buffer[1] = MBA_L_CHR(hi);
		buffer[2] = MBA_B_CHR(lo);
		buffer[3] = MBA_L_CHR(lo);
		buffer[4] = 0;
		mba_send_string(buffer);
	}
	uint8_t lrc0 = lrc;
	lrc = (uint8_t) ( (-((int8_t)lrc) ));
	buffer[0] = MBA_B_CHR(lrc);
	buffer[1] = MBA_L_CHR(lrc);
#if defined(TEST01)
	printf("%s:%i lrc=0x%02x lrc0=0x%02x x=0x%02x\n", __FUNCTION__, __LINE__, lrc, lrc0, lrc + lrc0);
#endif
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

#if defined(TEST01)

void main()
{
	int rc;
	vm_word_t values[3];
	values[0] = 0x1020;
	values[1] = 0x3040;
	values[2] = 0x5060;
	rc = mba_wr_reg(1, 1, 40000, 3, values);
	printf("%s:%i rc=%i\n", __FUNCTION__, __LINE__, rc);

}

#endif





