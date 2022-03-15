void setup() {

  // We know that TX will be the sender and RX the receiver
  DDRD = 0x08;

  // Set up UART in Synchronous mode
  // UCSRnA is a register full of flags that get set. We don't set them manually.
  UCSR1B |= 0x18; // USART receiver enable, USART transmitter enable
  UCSR1C |= 0x36; // Synchronous USART, 8-bit word size

  // Set Baud Rate
  // Baud Rate =  16Mhz / (16 * (UBBR + 1))
  // We want 9600, therefore, UBBR = (16,000,000 / (16 * 9,600)) + 1 = 103
  // Only need to write UBRR0L
  UBRR1L |= 0x67;

  //Serial.begin(9600);
  Serial1.begin(9600);
}

void loop() {

  //static unsigned int x = 0;
  //static unsigned char nums[9] = {0xFF, 0xFE, 0xFD, 0xFC, 0xFB, 0xFA, 0xF9, 0xF8, 0xF7};

  // Wait until receive complete
  while(!(UCSR1A & (1 << 7)));

  // Read from the register like so
  /* 
   * Note that data is received LSB first 
   */
  unsigned char var = UDR1;

  //unsigned char buf_inst = nums[x % 9];
  // Write to this register to kick off a transmission
  /* 
   * Note that data is transmitted LSB first 
   */
  if(var == 0x00) {
    UDR1 = 0xFF;
  } else if (var == 0x01) {
    UDR1 = 0xFE;
  } else if (var == 0x02) {
    UDR1 = 0xFD;
  } else if (var == 0x03) {
    UDR1 = 0xFC;
  } else if (var == 0x04) {
    UDR1 = 0xFB;
  } else if (var == 0x05) {
    UDR1 = 0xFA;
  } else if (var == 0x06) {
    UDR1 = 0xF9;
  } else if (var == 0x07) {
    UDR1 = 0xF8;
  } else if (var == 0x08) {
    UDR1 = 0xF7;
  }
  //Serial.println(x % 9);

  // Wait until transmit complete
  while(!(UCSR1A & (1 << 6)));

  // Clear transmission complete flag
  UCSR1A |= 0x40;

  // Wait 100ms
  //delay(100);

  // Increment x
  //++x;

}
