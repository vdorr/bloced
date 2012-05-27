
/** @file */ 

#ifndef __ARDUINO_IOWRAP_H__
#define __ARDUINO_IOWRAP_H__

#include "vm.h"

/**
	read digital input
	@param nr number of pin
*/
_VM_EXPORT_ vm_word_t d_in(vm_word_t nr);

/**
	write digital output
	@param nr number of pin
	@param v output value 0..1
*/
_VM_EXPORT_ void d_out(vm_word_t nr, vm_word_t v);


/**
	read analog input
	@param nr number of pin
	@param a_ref ADC reference voltage
	    0 DEFAULT: the default analog reference of 5 volts (on 5V Arduino boards) or 3.3 volts (on 3.3V Arduino boards)
	    1 INTERNAL: an built-in reference, equal to 1.1 volts on the ATmega168 or ATmega328 and 2.56 volts on the ATmega8 (not available on the Arduino Mega)
	    2 INTERNAL1V1: a built-in 1.1V reference (Arduino Mega only)
	    3 INTERNAL2V56: a built-in 2.56V reference (Arduino Mega only)
	    4 EXTERNAL: the voltage applied to the AREF pin (0 to 5V only) is used as the reference. 
	@return analog reading 0..1023
*/
_VM_EXPORT_ vm_word_t a_in(vm_word_t nr);

/**
	write analog output
	@param nr number of pin
	@param dc output value from 0 (always off) to 255 (always on)
*/
_VM_EXPORT_ void a_out(vm_word_t nr, vm_word_t dc);

/**
	set port as digital input
	@param nr number of pin
*/
_VM_EXPORT_ void set_d_in(vm_word_t nr);

/**
	set port as digital output
	@param nr number of pin
*/
_VM_EXPORT_ void set_d_out(vm_word_t nr);

/**
	set port as analog input
	@param nr number of pin
*/
_VM_EXPORT_ void set_a_in(vm_word_t nr);

/**
	set port as analog output
	@param nr number of pin
*/
_VM_EXPORT_ void set_a_out(vm_word_t nr);

/**
	return number of milliseconds since start of machine
*/
_VM_EXPORT_ vm_dword_t time_ms();

/**
	return number of microseconds since start of machine
*/
_VM_EXPORT_ vm_dword_t time_us();

///**
//	return number of microseconds since start of machine
//*/
//_VM_EXPORT_ void print(vm_word_t s);

/**
	configure serial channel
	@param ch number of serial channel
	@param speed baudrate
*/
_VM_EXPORT_ void start_serial(vm_word_t ch, vm_word_t speed);


_VM_EXPORT_ void seed_rnd(vm_word_t seed);

_VM_EXPORT_ vm_word_t rnd(vm_word_t max);

#endif

