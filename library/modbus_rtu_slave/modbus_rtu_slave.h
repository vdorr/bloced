
#ifndef __MODBUS_RTU_SLAVE__
#define __MODBUS_RTU_SLAVE__

/* 
 * configure_mb_slave(baud, parity, tx_en_pin)
 *
 * sets the communication parameters for of the serial line.
 *
 * baud: baudrate in bps (typical values 9600, 19200... 115200)
 * parity: a single character sets the parity mode (character frame format): 
 *         'n' no parity (8N1); 'e' even parity (8E1), 'o' for odd parity (8O1).
 * tx_en_pin: arduino pin number that controls transmision/reception
 *        of an external half-duplex device (e.g. a RS485 interface chip).
 *        0 or 1 disables this function (for a two-device network)
 *        >2 for point-to-multipoint topology (e.g. several arduinos)
 */
void configure_mb_slave(uint8_t channel, long baud, char parity, char txenpin,
	int16_t* registers);

/*
 * update_mb_slave(slave_id, holding_regs_array, number_of_regs)
 * 
 * checks if there is any valid request from the modbus master. If there is,
 * performs the action requested
 * 
 * slave: slave id (1 to 127)
 * regs: an array with the holding registers. They start at address 1 (master point of view)
 * regs_size: total number of holding registers.
 * returns: 0 if no request from master,
 * 	NO_REPLY (-1) if no reply is sent to the master
 * 	an exception code (1 to 4) in case of a modbus exceptions
 * 	the number of bytes sent as reply ( > 4) if OK.
 */
int update_mb_slave(uint8_t channel, unsigned char slave, int *regs,
	unsigned int regs_size);

#endif

