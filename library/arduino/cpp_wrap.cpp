
#include "Arduino.h"
#include "vm.h"

extern "C" void serial_begin(vm_word_t ch, vm_word_t speed)
{
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
‎#if 0
extern "C" void probe_bool(vm_word_t probe_id, vm_bool_t value)
{
	Serial.print(probe_id, HEX);
	Serial.print("=");
	Serial.print(value, HEX);
	Serial.println(value);
}

extern "C" void probe_char(vm_word_t probe_id, vm_char_t value)
{
	Serial.print(probe_id, HEX);
	Serial.print("=");
	Serial.print(value, HEX);
	Serial.println(value);
}

extern "C" void probe_word(vm_word_t probe_id, vm_word_t value)
{
	Serial.print(probe_id, HEX);
	Serial.print("=");
	Serial.print(value, HEX);
	Serial.println(value);
}

extern "C" void probe_dword(vm_word_t probe_id, vm_dword_t value)
{
	Serial.print(probe_id, HEX);
	Serial.print("=");
	Serial.print(value, HEX);
	Serial.println(value);
}

#endif
