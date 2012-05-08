
#include "Arduino.h"
#include "iowrap.h"

/*
void init(void);

void pinMode(uint8_t, uint8_t);
void digitalWrite(uint8_t, uint8_t);
int digitalRead(uint8_t);
int analogRead(uint8_t);
void analogReference(uint8_t mode);
void analogWrite(uint8_t, int);

unsigned long millis(void);
unsigned long micros(void);
void delay(unsigned long);
void delayMicroseconds(unsigned int us);
unsigned long pulseIn(uint8_t pin, uint8_t state, unsigned long timeout);

void shiftOut(uint8_t dataPin, uint8_t clockPin, uint8_t bitOrder, uint8_t val);
uint8_t shiftIn(uint8_t dataPin, uint8_t clockPin, uint8_t bitOrder);
*/

vm_word_t d_in(vm_word_t nr)
{
	return digitalRead(nr);
}

void d_out(vm_word_t nr, vm_word_t v)
{
	digitalWrite(nr, v);
}

vm_word_t a_in(vm_word_t nr/*, vm_word_t a_ref*/)
{
	/*analogReference(a_ref);*/
	return analogRead(nr);
}

void a_out(vm_word_t nr, vm_word_t dc)
{
	analogWrite(nr, dc);/* 0..255 */
}

void set_d_in(vm_word_t nr)
{
	pinMode(nr, INPUT);
}

void set_d_out(vm_word_t nr)
{
	pinMode(nr, OUTPUT);
}

void set_a_in(vm_word_t nr)
{
	pinMode(nr, INPUT);
}

void set_a_out(vm_word_t nr)
{
	pinMode(nr, OUTPUT);
}

vm_dword_t time_ms()
{
	return millis();
}

vm_dword_t time_us()
{
	return micros();
}

