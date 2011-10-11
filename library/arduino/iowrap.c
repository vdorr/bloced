
/* ------------------------------------------------------------------------ */

#define _VM_EXPORT_

_VM_EXPORT_ vm_word_t d_in(vm_word_t nr);
_VM_EXPORT_ void d_out(vm_word_t nr, vm_word_t v);
_VM_EXPORT_ vm_word_t a_in(vm_word_t nr, vm_word_t a_ref);
_VM_EXPORT_ void a_out(vm_word_t nr/*, vm_word_t f*/, vm_word_t dc);

_VM_EXPORT_ vm_dword_t time_ms(void);
_VM_EXPORT_ vm_dword_t time_us(void);

/* _VM_EXPORT_ const vm_word_t = INTERNAL; */

/* ------------------------------------------------------------------------ */

#define IF_LAZY_INIT	if

#define IF_LAZY_INIT()	if (1)

#define DIN_MAP(nr)	(nr)
#define DOUT_MAP(nr)	(nr)
#define AIN_MAP(nr)	(nr)
#define AOUT_MAP(nr)	(nr)



#define PINMODE_UNINITIALIZED	0
#define PINMODE_DIGITAL_IN	1
#define PINMODE_DIGITAL_OUT	2
#define PINMODE_ANALOG_IN	3
#define PINMODE_ANALOG_OUT	4

static unsigned char pin_mode[20] =
{
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
	PINMODE_UNINITIALIZED,
};

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
/* ------------------------------------------------------------------------ */

vm_word_t d_in(vm_word_t nr)
{
	IF_LAZY_INIT ( pin_mode[DIN_MAP(nr)] != PINMODE_DIGITAL_IN )
	{
		pinMode(nr, INPUT);
		pin_mode[DIN_MAP(nr)] = PINMODE_DIGITAL_IN;
	}
	return digitalRead(nr);
}

/* ------------------------------------------------------------------------ */

void d_out(vm_word_t nr, vm_word_t v)
{
	IF_LAZY_INIT ( pin_mode[DOUT_MAP(nr)] != PINMODE_DIGITAL_OUT )
	{
		pinMode(nr, OUTPUT);
		pin_mode[DOUT_MAP(nr)] = PINMODE_DIGITAL_OUT;
	}
	digitalWrite(nr, v);
}

/* ------------------------------------------------------------------------ */

/*
    DEFAULT: the default analog reference of 5 volts (on 5V Arduino boards) or 3.3 volts (on 3.3V Arduino boards)
    INTERNAL: an built-in reference, equal to 1.1 volts on the ATmega168 or ATmega328 and 2.56 volts on the ATmega8 (not available on the Arduino Mega)
    INTERNAL1V1: a built-in 1.1V reference (Arduino Mega only)
    INTERNAL2V56: a built-in 2.56V reference (Arduino Mega only)
    EXTERNAL: the voltage applied to the AREF pin (0 to 5V only) is used as the reference. 
*/

vm_word_t a_in(vm_word_t nr, vm_word_t a_ref)
{
	IF_LAZY_INIT ( pin_mode[AIN_MAP(nr)] != PINMODE_ANALOG_IN )
	{
		pinMode(nr, INPUT);
		analogReference(a_ref);
		pin_mode[AIN_MAP(nr)] = PINMODE_ANALOG_IN;
	}
	return analogRead(nr);
}

/* ------------------------------------------------------------------------ */

void a_out(vm_word_t nr/*, vm_word_t f*/, vm_word_t dc)
{
	IF_LAZY_INIT ( pin_mode[AOUT_MAP(nr)] != PINMODE_ANALOG_OUT )
	{
		pinMode(nr, OUTPUT);
		pin_mode[AOUT_MAP(nr)] = PINMODE_ANALOG_OUT;
	}
	analogWrite(nr, dc);/* 0..255 */
}

/* ------------------------------------------------------------------------ */


