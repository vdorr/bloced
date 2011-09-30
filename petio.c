
/* ------------------------------------------------------------------------ */

void di_enable(int nr);
void di_disable(int nr);
void di_pull_resistor(int nr, int enabled);
int di_read(int nr);

/* ------------------------------------------------------------------------ */

void do_enable(int nr);
void do_disable(int nr);
void do_pull_resistor(int nr, int enabled);
int do_read(int nr);
int do_write(int nr, int value);
int do_write3s(int nr, int value);
int do_h_write(int nra, int nrb, int value);

/* ------------------------------------------------------------------------ */

void ai_enable(int nr);
void ai_disable(int nr);
void ai_set_resolution(int nr, int bits);
int ai_get_resolution(int nr);
int ai_read(int nr);
void ai_start_conversion(int nr);
int ai_get_conversion_done(int nr);

/* ------------------------------------------------------------------------ */

void tmr_enable(int nr);
void tmr_disable(int nr);
void tmr_set_divider(int nr, int divisor);
int tmr_get_divider(int nr);
void tmr_set_preset(int nr, int preset);
int tmr_get_preset(int nr);
void tmr_clear(int nr);
int tmr_get_value(int nr);

/* ------------------------------------------------------------------------ */

void uart_enable(int nr, int baudrate, int bits, int parity, int stopbits);
void uart_disable(int nr);
void uart_write(int nr, char* data, int length);
void uart_write_string(int nr, char* data);
int uart_read(int nr, char* data, int length, int timeout);

/* ------------------------------------------------------------------------ */

int e2_read(int addr);
int e2_write(int addr, int value);

/* ------------------------------------------------------------------------ */

