
#include "Arduino.h"
#include "vm.h"
#include "iowrap.h"

extern "C" void serial_begin(vm_word_t ch, vm_word_t speed)
{
#if defined(DBG_ENABLE_GATEWAY) && DBG_ENABLE_GATEWAY >= 1
	return;
#endif
#if 1
	Serial.begin(speed);
#else
	switch (ch)
	{
	case 1 :
		Serial1.begin(speed);
		break;
	case 2 :
		Serial2.begin(speed);
		break;
	case 3 :
		Serial3.begin(speed);
		break;
	case 4 :
		Serial4.begin(speed);
		break;
	default :
		break;
	}
#endif
}


#if 1

//#ifndef ARDUINO
//#define ARDUINO 101
//#define ARDUINO_WAS_UDNEFINED
//#endif
#include "Firmata.h"
//#ifdef ARDUINO_WAS_UDNEFINED
//#undef ARDUINO
//#endif

#if defined(DBG_ENABLE_GATEWAY) && DBG_ENABLE_GATEWAY >= 1

#define PROBE_CBUFFER_SIZE	(64)
//static uint8_t cbuffer[sizeof(vm_word_t)+PROBE_CBUFFER_SIZE];
static uint8_t cbuffer[PROBE_CBUFFER_SIZE];
typedef uint16_t cbuff_ptr_t;
static volatile cbuff_ptr_t cbuff_ptr = 0;
static volatile cbuff_ptr_t cbuff_count = 0;

#define PROBE_IMPL 2

//#if PROBE_IMPL == 2
//typedef struct {
//	unsigned int bytes : 2;
//} probe_frame_t;
//#endif

#if PROBE_IMPL == 2
	typedef struct {
		vm_bool_t value;
		vm_probe_t id;
	} probe_bool_t;
	typedef struct {
		vm_char_t value;
		vm_probe_t id;
	} probe_char_t;
	typedef struct {
		vm_word_t value;
		vm_probe_t id;
	} probe_word_t;
	typedef struct {
		vm_dword_t value;
		vm_probe_t id;
	} probe_dword_t;


#define PUT_PROBE(p, cbuff_ptr, cbuff_count) \
do { \
	for ( int i = 0; i < (sizeof((p).value)); i++) { \
		cbuffer[cbuff_ptr] = ((uint8_t*)&((p).value))[i]; \
		cbuff_ptr = (cbuff_ptr + 1) & (((cbuff_ptr_t)PROBE_CBUFFER_SIZE) - 1); \
	} \
	cbuff_count = (cbuff_count + sizeof((p).value) + 1) & (((cbuff_ptr_t)PROBE_CBUFFER_SIZE) - 1); \
	cbuffer[cbuff_ptr] = p.id; \
	cbuff_ptr = (cbuff_ptr + 1) & (((cbuff_ptr_t)PROBE_CBUFFER_SIZE) - 1); \
} while ( 0 )

#endif

extern "C" void probe_bool(vm_probe_t probe_id, vm_bool_t value)
{
#if PROBE_IMPL == 1
	Serial.print(probe_id, HEX);
	Serial.print("=");
	Serial.print(value, HEX);
	Serial.println(value);
#elif PROBE_IMPL == 2
	probe_bool_t p = { value, probe_id };
	PUT_PROBE(p, cbuff_ptr, cbuff_count);
#else
#endif
}

extern "C" void probe_char(vm_probe_t probe_id, vm_char_t value)
{
#if PROBE_IMPL == 1
	Serial.print(probe_id, HEX);
	Serial.print("=");
	Serial.print(value, HEX);
	Serial.println(value);
#elif PROBE_IMPL == 2
	probe_char_t p = { value, probe_id };
	PUT_PROBE(p, cbuff_ptr, cbuff_count);
#else
#endif
}

extern "C" void probe_word(vm_probe_t probe_id, vm_word_t value)
{
#if PROBE_IMPL == 1
	Serial.print(probe_id, HEX);
	Serial.print("=");
	Serial.print(value, HEX);
	Serial.println(value);
#elif PROBE_IMPL == 2
	probe_word_t p = { value, probe_id };
	PUT_PROBE(p, cbuff_ptr, cbuff_count);
#else
#endif
}

extern "C" void probe_dword(vm_probe_t probe_id, vm_dword_t value)
{
#if PROBE_IMPL == 1
	Serial.print(probe_id, HEX);
	Serial.print("=");
	Serial.print(value, HEX);
	Serial.println(value);
#elif PROBE_IMPL == 2
	probe_dword_t p = { value, probe_id };
	PUT_PROBE(p, cbuff_ptr, cbuff_count);
#else
#endif
}

extern "C" void probes_init()
{
	cbuff_count = 0;
	cbuff_ptr = 0;
	Serial.begin(9600);//TODO TODO TODO we need it configurable from UI!
	Serial.write((uint8_t)0xff);
	Serial.write((uint8_t)0x00);
	delay(100);
#if 0
	Firmata.begin(9600);
#endif
}

extern "C" void probes_shutdown()
{
}

//#if 1

//#if 0
//static const uint8_t PROGMEM dscrc_table[] = {
//      0, 94,188,226, 97, 63,221,131,194,156,126, 32,163,253, 31, 65,
//    157,195, 33,127,252,162, 64, 30, 95,  1,227,189, 62, 96,130,220,
//     35,125,159,193, 66, 28,254,160,225,191, 93,  3,128,222, 60, 98,
//    190,224,  2, 92,223,129, 99, 61,124, 34,192,158, 29, 67,161,255,
//     70, 24,250,164, 39,121,155,197,132,218, 56,102,229,187, 89,  7,
//    219,133,103, 57,186,228,  6, 88, 25, 71,165,251,120, 38,196,154,
//    101, 59,217,135,  4, 90,184,230,167,249, 27, 69,198,152,122, 36,
//    248,166, 68, 26,153,199, 37,123, 58,100,134,216, 91,  5,231,185,
//    140,210, 48,110,237,179, 81, 15, 78, 16,242,172, 47,113,147,205,
//     17, 79,173,243,112, 46,204,146,211,141,111, 49,178,236, 14, 80,
//    175,241, 19, 77,206,144,114, 44,109, 51,209,143, 12, 82,176,238,
//     50,108,142,208, 83, 13,239,177,240,174, 76, 18,145,207, 45,115,
//    202,148,118, 40,171,245, 23, 73,  8, 86,180,234,105, 55,213,139,
//     87,  9,235,181, 54,104,138,212,149,203, 41,119,244,170, 72, 22,
//    233,183, 85, 11,136,214, 52,106, 43,117,151,201, 74, 20,246,168,
//    116, 42,200,150, 21, 75,169,247,182,232, 10, 84,215,137,107, 53};

//uint8_t crc8( uint8_t *addr, uint8_t len)
//{
//	uint8_t crc = 0;

//	while (len--) {
//		crc = pgm_read_byte(dscrc_table + (crc ^ *addr++));
//	}
//	return crc;
//}
//#else
uint8_t crc8( uint8_t *addr, uint8_t len, uint8_t crc)
{
	
	while (len--) {
		uint8_t inbyte = *addr++;
		for (uint8_t i = 8; i; i--) {
			uint8_t mix = (crc ^ inbyte) & 0x01;
			crc >>= 1;
			if (mix) crc ^= 0x8C;
			inbyte >>= 1;
		}
	}
	return crc;
}
//#endif

void send_cbuffer()
{
	uint8_t crc;
	uint8_t op = 0x10;
	uint8_t len = cbuff_count+3;//XXX max 256bytes!! 3 is for op, len, crc
	Serial.write(op);
	crc = crc8(&op, 1, 0);
	Serial.write(len);
	crc = crc8(&len, 1, crc);

	for (uint8_t j = 0; j < cbuff_count - cbuff_ptr; j++)
	{
		uint8_t i = j + cbuff_ptr;
		if ( cbuffer[i] == 0xff )
		{
			Serial.write((uint8_t)0xff);
		}
		Serial.write(cbuffer[i]);
		crc = crc8(&cbuffer[i], 1, crc);
	}

	for (uint8_t i = 0; i < cbuff_ptr; i++)
	{
		if ( cbuffer[i] == 0xff )
		{
			Serial.write((uint8_t)0xff);
		}
		Serial.write(cbuffer[i]);
		crc = crc8(&cbuffer[i], 1, crc);
	}
	Serial.write(crc);
}

extern "C" void probes_transmit()//TODO add timestamp as argument
{
	Serial.write((uint8_t)0xff);
	Serial.write((uint8_t)0x00);

	if ( cbuff_count )
	{
//TODO maybe request to send channel number


		send_cbuffer();
		cbuff_count = 0;
		cbuff_ptr = 0;
	}
	else
	{
//TODO heartbeat		Serial.write((uint8_t)0x20);
	}
	Serial.write((uint8_t)0xff);
	Serial.write((uint8_t)0x01);
}

#endif /* #if defined(DBG_ENABLE_GATEWAY) && DBG_ENABLE_GATEWAY >= 1 */

extern "C" void vm_idle_hook()
{
#if defined(DBG_ENABLE_GATEWAY) && DBG_ENABLE_GATEWAY >= 1
	probes_transmit();
#endif
}

extern "C" void vm_init_hook()
{
#if defined(DBG_ENABLE_GATEWAY) && DBG_ENABLE_GATEWAY >= 1
	probes_init();
#endif
}

#endif

