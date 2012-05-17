
#include "Arduino.h"
#include "vm.h"

extern "C" int mba_send_string(const uint8_t* buffer)
{
	Serial.print((const char*)buffer);
	return 0;
}

