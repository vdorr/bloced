
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
static cbuff_ptr_t cbuff_ptr = 0;
static cbuff_ptr_t cbuff_count = 0;

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
	for ( int i = 0; i < sizeof(p); i++) { \
		cbuff_ptr = (cbuff_ptr + 1) & (((cbuff_ptr_t)PROBE_CBUFFER_SIZE) - 1); \
		cbuffer[cbuff_ptr] = ((uint8_t*)&p)[i]; \
	} \
	cbuff_count = (cbuff_count + sizeof(p)) & (((cbuff_ptr_t)PROBE_CBUFFER_SIZE) - 1); \
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
	probe_bool_t p = { probe_id, value };
	PUT_PROBE(p, cbuff_ptr, cbuff_count);
//	for ( int i = 0; i < sizeof(p); i++)
//	{
//		cbuff_ptr = (cbuff_ptr + 1) & (((cbuff_ptr_t)PROBE_CBUFFER_SIZE) - 1);
//		cbuffer[cbuff_ptr] = ((uint8_t*)&p)[i];
//	}
//	cbuff_count = (cbuff_count + sizeof(p)) & (((cbuff_ptr_t)PROBE_CBUFFER_SIZE) - 1);
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
	probe_char_t p = { probe_id, value };
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
	probe_word_t p = { probe_id, value };
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
	probe_dword_t p = { probe_id, value };
	PUT_PROBE(p, cbuff_ptr, cbuff_count);
#else
#endif
}

extern "C" void probes_init()
{
	cbuff_ptr = 0;
	Serial.begin(9600);//TODO TODO TODO we need it configurable from UI!
	Serial.write((uint8_t)0xff);
	Serial.write((uint8_t)0x00);
	delay(100);
	Firmata.begin(9600);
}

extern "C" void probes_shutdown()
{
}

extern "C" void probes_transmit()//TODO add timestamp as argument
{
#if 0
	Serial.write((uint8_t)0xff);
	Serial.write((uint8_t)0x01);
#else
	Serial.write((uint8_t)0xff);
	Serial.write((uint8_t)0x00);
	//probably no need to escape data, because Firmata's 7bit encoding
//sendSysex(byte command, byte bytec, byte* bytev) 
	if ( cbuff_count )
	{
//		Firmata.sendSysex(0x10, cbuff_count/*XXX*/, (byte*)cbuffer);

//TODO drop Firmata
//TODO add CRC!!! and maybe request to send channel number
		Firmata.sendSysex(0x10, cbuff_ptr, (byte*)cbuffer);
		Firmata.sendSysex(0x11, cbuff_count - cbuff_ptr, (byte*)cbuffer + cbuff_ptr);

		cbuff_count = 0;
		cbuff_ptr = 0;
	}
	else
	{
		//send heartbeat
		Firmata.sendSysex(0x20, 0, (byte*)"");
	}
	Serial.write((uint8_t)0xff);
	Serial.write((uint8_t)0x01);
#endif
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

