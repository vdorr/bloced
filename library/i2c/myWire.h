/*
  TwoWire.h - TWI/I2C library for Arduino & Wiring
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

#ifndef TwoWire_h
#define TwoWire_h

#include <inttypes.h>
#include <stdlib.h>

#include "../../../target/arduino/include/vm.h"

#define BUFFER_LENGTH 32

static void Wire_onRequestService(void);
static void Wire_onReceiveService(uint8_t*, int);

void Wire_begin(uint8_t);
void Wire_beginTransmission(uint8_t);
uint8_t Wire_endTransmission(uint8_t);
uint8_t Wire_requestFrom(uint8_t, uint8_t, uint8_t);

size_t Wire_write_char(uint8_t);
size_t Wire_write(const uint8_t *, size_t);

int Wire_available(void);
int Wire_read(void);
int Wire_peek(void);
void Wire_flush(void);
void Wire_onReceive( void (*)(int) );
void Wire_onRequest( void (*)(void) );

#endif

