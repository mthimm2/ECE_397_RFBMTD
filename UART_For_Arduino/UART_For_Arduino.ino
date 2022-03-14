void setup() {

  // We know that TX will be the sender and RX the receiver
  DDRD = 0x02;

  // Set up UART in Synchronous mode
  // UCSRnA is a register full of flags that get set. We don't set them manually.
  UCSR0B |= 0x18; // USART receiver enable, USART transmitter enable
  UCSR0C |= 0x06; // Synchronous USART, 8-bit word size

  // Set Baud Rate
  // Baud Rate =  16Mhz / (16 * (UBBR + 1))
  // We want 9600, therefore, UBBR = (16,000,000 / (16 * 9,600)) + 1 = 103
  // Only need to write UBRR0L
  UBRR0L |= 0x67;

  Serial.begin(9600);
}

void loop() {

  static unsigned int x = 0;
  static unsigned char nums[9] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};

  // Wait until receive complete
  //while(!(UCSR0A & (1 << 7)));

  // Read from the register like so
  /* 
   * Note that data is received LSB first 
   */
  //unsigned char var = UDR0;

  //Serial.println(var);

  unsigned char buf_inst = nums[x % 9];
  // Write to this register to kick off a transmission
  /* 
   * Note that data is transmitted LSB first 
   */
  UDR0 = nums[x % 9];
  Serial.println(x % 9);

  // Wait until transmit complete
  while(!(UCSR0A & (1 << 6)));

  // Clear transmission complete flag
  UCSR0A |= 0x40;

  // Increment x
  ++x;

}
