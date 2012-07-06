/*
TwoWire.cpp - TWI/I2C library for Wiring & Arduino
Copyright (c) 2006 Nicholas Zambetti. All right reserved.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

Modified 2012 by Todd Krein (todd@krein.org) to implement repeated starts

Kidnapped 2012 by vdorr

*/


// avr-gcc -std=c99 -mmcu=atmega328p -DF_CPU=16000000L twi.c twi_tool.c

#include <stdlib.h>
#include <inttypes.h>
#include <string.h>
#include "twi.h"

#define BUFFER_LENGTH 32

//private:
    static uint8_t rxBuffer[];
    static uint8_t rxBufferIndex;
    static uint8_t rxBufferLength;

    static uint8_t txAddress;
    static uint8_t txBuffer[];
    static uint8_t txBufferIndex;
    static uint8_t txBufferLength;

    static uint8_t transmitting;
    static void (*user_onRequest)(void);
    static void (*user_onReceive)(int);
    static void onRequestService(void);
    static void onReceiveService(uint8_t*, int);

//public:

    void begin(uint8_t);

    void beginTransmission(uint8_t);

    uint8_t endTransmission(uint8_t);
    uint8_t requestFrom(uint8_t, uint8_t, uint8_t);

size_t write(const uint8_t *, size_t);
int available(void);
int read(void);
int peek(void);
void flush(void);
    void onReceive( void (*)(int) );
    void onRequest( void (*)(void) );










// Initialize Class Variables //////////////////////////////////////////////////
void i2c_subsystem_init()
{
memset(rxBuffer, BUFFER_LENGTH, 0);
rxBufferIndex = 0;
rxBufferLength = 0;

txAddress = 0;
memset(txBuffer, BUFFER_LENGTH, 0);
txBufferIndex = 0;
txBufferLength = 0;

transmitting = 0;
}


/*void (*user_onRequest)(void);*/
/*void (*user_onReceive)(int);*/

void begin(uint8_t address)
{
  twi_setAddress(address);
  twi_attachSlaveTxEvent(onRequestService);
  twi_attachSlaveRxEvent(onReceiveService);

  rxBufferIndex = 0;
  rxBufferLength = 0;

  txBufferIndex = 0;
  txBufferLength = 0;

  twi_init();

}

uint8_t requestFrom(uint8_t address, uint8_t quantity, uint8_t sendStop)//sendStop default to True
{
  // clamp to buffer length
  if(quantity > BUFFER_LENGTH){
    quantity = BUFFER_LENGTH;
  }
  // perform blocking read into buffer
  uint8_t read = twi_readFrom(address, rxBuffer, quantity);
  // set rx buffer iterator vars
  rxBufferIndex = 0;
  rxBufferLength = read;

  return read;
}

void beginTransmission(uint8_t address)
{
  // indicate that we are transmitting
  transmitting = 1;
  // set address of targeted slave
  txAddress = address;
  // reset tx buffer iterator vars
  txBufferIndex = 0;
  txBufferLength = 0;
}

//
// Originally, 'endTransmission' was an f(void) function.
// It has been modified to take one parameter indicating
// whether or not a STOP should be performed on the bus.
// Calling endTransmission(false) allows a sketch to
// perform a repeated start.
//
// WARNING: Nothing in the library keeps track of whether
// the bus tenure has been properly ended with a STOP. It
// is very possible to leave the bus in a hung state if
// no call to endTransmission(true) is made. Some I2C
// devices will behave oddly if they do not see a STOP.
//
uint8_t endTransmission(uint8_t sendStop)//sendStop default to True
{
  // transmit buffer (blocking)
  int8_t ret = twi_writeTo(txAddress, txBuffer, txBufferLength, 1, sendStop);
  // reset tx buffer iterator vars
  txBufferIndex = 0;
  txBufferLength = 0;
  // indicate that we are done transmitting
  transmitting = 0;
  return ret;
}

// must be called in:
// slave tx event callback
// or after beginTransmission(address)
size_t write(uint8_t data)
{
  if(transmitting){
  // in master transmitter mode
    // don't bother if buffer is full
    if(txBufferLength >= BUFFER_LENGTH){
      setWriteError();
      return 0;
    }
    // put byte in tx buffer
    txBuffer[txBufferIndex] = data;
    ++txBufferIndex;
    // update amount in buffer
    txBufferLength = txBufferIndex;
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
size_t write(const uint8_t *data, size_t quantity)
{
  if(transmitting){
  // in master transmitter mode
    for(size_t i = 0; i < quantity; ++i){
      write(data[i]);
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
int available(void)
{
  return rxBufferLength - rxBufferIndex;
}

// must be called in:
// slave rx event callback
// or after requestFrom(address, numBytes)
int read(void)
{
  int value = -1;
  
  // get each successive byte on each call
  if(rxBufferIndex < rxBufferLength){
    value = rxBuffer[rxBufferIndex];
    ++rxBufferIndex;
  }

  return value;
}

// must be called in:
// slave rx event callback
// or after requestFrom(address, numBytes)
int peek(void)
{
  int value = -1;
  
  if(rxBufferIndex < rxBufferLength){
    value = rxBuffer[rxBufferIndex];
  }

  return value;
}

void flush(void)
{
  // XXX: to be implemented.
}

// behind the scenes function that is called when data is received
void onReceiveService(uint8_t* inBytes, int numBytes)
{
  // don't bother if user hasn't registered a callback
  if(!user_onReceive){
    return;
  }
  // don't bother if rx buffer is in use by a master requestFrom() op
  // i know this drops data, but it allows for slight stupidity
  // meaning, they may not have read all the master requestFrom() data yet
  if(rxBufferIndex < rxBufferLength){
    return;
  }
  // copy twi rx buffer into local read buffer
  // this enables new reads to happen in parallel
  for(uint8_t i = 0; i < numBytes; ++i){
    rxBuffer[i] = inBytes[i];
  }
  // set rx iterator vars
  rxBufferIndex = 0;
  rxBufferLength = numBytes;
  // alert user program
  user_onReceive(numBytes);
}

// behind the scenes function that is called when data is requested
void onRequestService(void)
{
  // don't bother if user hasn't registered a callback
  if(!user_onRequest){
    return;
  }
  // reset tx buffer iterator vars
  // !!! this will kill any pending pre-master sendTo() activity
  txBufferIndex = 0;
  txBufferLength = 0;
  // alert user program
  user_onRequest();
}

// sets function called on slave write
void onReceive( void (*function)(int) )
{
  user_onReceive = function;
}

// sets function called on slave read
void onRequest( void (*function)(void) )
{
  user_onRequest = function;
}

