/*
  TwoWire.cpp - TWI/I2C library for Wiring & Arduino
  Copyright (c) 2006 Nicholas Zambetti.  All right reserved.

  This library is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; either
  version 2.1 of the License, or (at your option) any later version.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with this library; if not, write to the Free Software
  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 
  Modified 2012 by Todd Krein (todd@krein.org) to implement repeated starts

  heavily modified by vdorr 2012

*/

#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include "twi_async.h"

#include "myWire.h"

uint8_t Wire_rxBuffer[BUFFER_LENGTH];
uint8_t Wire_rxBufferIndex = 0;
uint8_t Wire_rxBufferLength = 0;

uint8_t Wire_txAddress = 0;
uint8_t Wire_txBuffer[BUFFER_LENGTH];
uint8_t Wire_txBufferIndex = 0;
uint8_t Wire_txBufferLength = 0;

uint8_t Wire_transmitting = 0;//XXX this is probably pointless in master-only implementation
void (*Wire_user_onRequest)(void);
void (*Wire_user_onReceive)(int);


/*void i2c_init(vm_word_t ch, vm_word_t addr, vm_word_t speed, vm_word_t* st);*/

/*void i2c_snd(vm_bool_t en, vm_word_t addr, vm_bool_t* eno, vm_word_t* err,*/
/*	vm_word_t bytes_in_count, vm_char_t* bytes);*/

/*void i2c_rcv(vm_bool_t en, vm_word_t addr, vm_bool_t* eno, vm_word_t* err,*/
/*	vm_word_t bytes_out_count, vm_char_t* bytes);*/

// -----------------------------------------------------------------------------------------------------------

void i2c_init(vm_word_t ch, vm_word_t addr, vm_word_t speed, vm_word_t* err)
{
	(void)ch;//TODO
	(void)speed;//TODO

	twi_setAddress(addr);

/*	Wire_rxBufferIndex = 0;*/
/*	Wire_rxBufferLength = 0;*/

/*	Wire_txBufferIndex = 0;*/
/*	Wire_txBufferLength = 0;*/

	twi_init();

	*err = 0;
}
/*	static uint8_t i2c_int_state = 0;*/

void i2c_snd(vm_bool_t en, vm_word_t addr,
	vm_char_t sti,
	vm_bool_t* eno,
	vm_word_t* err,
	vm_char_t* sto,
	vm_word_t bytes_in_count,
	vm_char_t* bytes)
{
	uint8_t ret;
	if (en || sti)
	{
		*sto = sti;
		if (twi_writeTo_async(sto, addr, bytes, bytes_in_count, 1, 1, &ret))
		{
//TODO timeout
			*eno = 0;
			*err = 0;
		}
		else
		{
			*eno = 1;
			*err = ret;
			return;
		}
	}
	*eno = 0;
	*err = 0;
}

void i2c_rcv(vm_bool_t en, vm_word_t addr, vm_bool_t* eno, vm_word_t* err,
	vm_word_t bytes_out_count, vm_char_t* bytes)
{
}

// -----------------------------------------------------------------------------------------------------------

/*uint8_t twi_readFromXXX(uint8_t address, uint8_t* data, uint8_t length, uint8_t sendStop)*/
/*{*/
/*	uint8_t state = 0;*/
/*	uint8_t rc;*/
/*	while (twi_readFrom_async(&state, address, data, length, sendStop, &rc));*/
/*	return rc;*/
/*}*/

/*uint8_t twi_writeToXXX(uint8_t address, uint8_t* data, uint8_t length, uint8_t wait, uint8_t sendStop)*/
/*{*/
/*	uint8_t state = 0;*/
/*	uint8_t rc;*/
/*	while (twi_writeTo_async(&state,address, data, length, wait, sendStop, &rc));*/
/*	return rc;*/
/*}*/

#if 0
void Wire_begin(uint8_t address)
{
  twi_setAddress(address);
  twi_attachSlaveTxEvent(Wire_onRequestService);
  twi_attachSlaveRxEvent(Wire_onReceiveService);

  Wire_rxBufferIndex = 0;
  Wire_rxBufferLength = 0;

  Wire_txBufferIndex = 0;
  Wire_txBufferLength = 0;

  twi_init();
}

uint8_t Wire_requestFrom(uint8_t address, uint8_t quantity, uint8_t sendStop)
{
  // clamp to buffer length
  if(quantity > BUFFER_LENGTH){
    quantity = BUFFER_LENGTH;
  }
  // perform blocking read into buffer
/*  uint8_t read = twi_readFrom(address, Wire_rxBuffer, quantity, sendStop);*/

	uint8_t state = 0;
	uint8_t read;
	while (twi_readFrom_async(&state, address, Wire_rxBuffer, quantity, sendStop, &read))
	{
		continue;
	}


  // set rx buffer iterator vars
  Wire_rxBufferIndex = 0;
  Wire_rxBufferLength = read;

  return read;
}

void Wire_beginTransmission(uint8_t address)
{
  // indicate that we are transmitting
  Wire_transmitting = 1;
  // set address of targeted slave
  Wire_txAddress = address;
  // reset tx buffer iterator vars
  Wire_txBufferIndex = 0;
  Wire_txBufferLength = 0;
}

//
//	Originally, 'endTransmission' was an f(void) function.
//	It has been modified to take one parameter indicating
//	whether or not a STOP should be performed on the bus.
//	Calling endTransmission(false) allows a sketch to 
//	perform a repeated start. 
//
//	WARNING: Nothing in the library keeps track of whether
//	the bus tenure has been properly ended with a STOP. It
//	is very possible to leave the bus in a hung state if
//	no call to endTransmission(true) is made. Some I2C
//	devices will behave oddly if they do not see a STOP.
//
uint8_t Wire_endTransmission(uint8_t sendStop)
{
  // transmit buffer (blocking)
/*  uint8_t ret = twi_writeTo(Wire_txAddress, Wire_txBuffer, Wire_txBufferLength, 1, sendStop);*/

	uint8_t state = 0;
	uint8_t ret;
	while (twi_writeTo_async(&state, Wire_txAddress, Wire_txBuffer, Wire_txBufferLength, 1, sendStop, &ret))
	{
		continue;
	}


  // reset tx buffer iterator vars
  Wire_txBufferIndex = 0;
  Wire_txBufferLength = 0;
  // indicate that we are done transmitting
  Wire_transmitting = 0;
  return ret;
}

// must be called in:
// slave tx event callback
// or after beginTransmission(address)
size_t Wire_write_char(uint8_t data)
{
  if(Wire_transmitting){
  // in master transmitter mode
    // don't bother if buffer is full
    if(Wire_txBufferLength >= BUFFER_LENGTH){
//XXX      setWriteError();
      return 0;
    }
    // put byte in tx buffer
    Wire_txBuffer[Wire_txBufferIndex] = data;
    ++Wire_txBufferIndex;
    // update amount in buffer   
    Wire_txBufferLength = Wire_txBufferIndex;
  }else{
  // in slave send mode
    // reply to master
    twi_transmit(&data, 1);
  }
  return 1;
}

// must be called in:
// slave tx event callback
// or after beginTransmission(address)
size_t Wire_write(const uint8_t *data, size_t quantity)
{
  if(Wire_transmitting){
  // in master transmitter mode
size_t i;
    for(i = 0; i < quantity; ++i){
      Wire_write_char(data[i]);
    }
  }else{
  // in slave send mode
    // reply to master
    twi_transmit(data, quantity);
  }
  return quantity;
}

// must be called in:
// slave rx event callback
// or after requestFrom(address, numBytes)
int Wire_available(void)
{
  return Wire_rxBufferLength - Wire_rxBufferIndex;
}

// must be called in:
// slave rx event callback
// or after requestFrom(address, numBytes)
int Wire_read(void)
{
  int value = -1;
  
  // get each successive byte on each call
  if(Wire_rxBufferIndex < Wire_rxBufferLength){
    value = Wire_rxBuffer[Wire_rxBufferIndex];
    ++Wire_rxBufferIndex;
  }

  return value;
}

// must be called in:
// slave rx event callback
// or after requestFrom(address, numBytes)
int Wire_peek(void)
{
  int value = -1;
  
  if(Wire_rxBufferIndex < Wire_rxBufferLength){
    value = Wire_rxBuffer[Wire_rxBufferIndex];
  }

  return value;
}

void Wire_flush(void)
{
  // XXX: to be implemented.
}

// behind the scenes function that is called when data is received
void Wire_onReceiveService(uint8_t* inBytes, int numBytes)
{
  // don't bother if user hasn't registered a callback
  if(!Wire_user_onReceive){
    return;
  }
  // don't bother if rx buffer is in use by a master requestFrom() op
  // i know this drops data, but it allows for slight stupidity
  // meaning, they may not have read all the master requestFrom() data yet
  if(Wire_rxBufferIndex < Wire_rxBufferLength){
    return;
  }
  // copy twi rx buffer into local read buffer
  // this enables new reads to happen in parallel
uint8_t i;
  for(i = 0; i < numBytes; ++i){
    Wire_rxBuffer[i] = inBytes[i];    
  }
  // set rx iterator vars
  Wire_rxBufferIndex = 0;
  Wire_rxBufferLength = numBytes;
  // alert user program
  Wire_user_onReceive(numBytes);
}

// behind the scenes function that is called when data is requested
void Wire_onRequestService(void)
{
  // don't bother if user hasn't registered a callback
  if(!Wire_user_onRequest){
    return;
  }
  // reset tx buffer iterator vars
  // !!! this will kill any pending pre-master sendTo() activity
  Wire_txBufferIndex = 0;
  Wire_txBufferLength = 0;
  // alert user program
  Wire_user_onRequest();
}

// sets function called on slave write
void Wire_onReceive( void (*function)(int) )
{
  Wire_user_onReceive = function;
}

// sets function called on slave read
void Wire_onRequest( void (*function)(void) )
{
  Wire_user_onRequest = function;
}

#endif

