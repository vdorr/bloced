
#include <WProgram.h>

#define CYCLE_TIME_MS	100

int main()
{

	init();

#include "task_vars.c"

	unsigned long t;

	for (;;)
	{
		t = millis() + CYCLE_TIME_MS;
#include "task_list.c"
		delay(t - millis());
	}

	return -1;
}
