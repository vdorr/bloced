
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
