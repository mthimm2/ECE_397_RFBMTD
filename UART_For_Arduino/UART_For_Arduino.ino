void setup() {

  // We know that TX will be the sender and RX the receiver
  DDRD |= 0x02;

  // Set up UART in Synchronous mode
  // UCSRnA is a register full of flags that get set. We don't set them manually.
  UCSR0B |= 0x18; // USART receiver enable, USART transmitter enable
  UCSR0C |= 0x06; // Synchronous USART, 8-bit word size

  // Set Baud Rate
  // Baud Rate =  16Mhz / (16 * (UBBR + 1))
  // We want 9600, therefore, UBBR = (16,000,000 / (16 * 9,600)) + 1 = 103
  // Only need to write UBRR0L
  UBRR0L |= 0x67;
}

void loop() {

  // Wait until receive complete
  while(!(UCSR0A & (1 << 7)));

  // Read from the register like so
  /* 
   * Note that data is received LSB first 
   */
  unsigned char var = UDR0;

  unsigned char x = 0xFF;
  // Write to this register to kick off a transmission
  /* 
   * Note that data is transmitted LSB first 
   */
  UDR0 = x;

  // Wait until transmit complete
  while(!(UCSR0A & (1 << 6)));

}
