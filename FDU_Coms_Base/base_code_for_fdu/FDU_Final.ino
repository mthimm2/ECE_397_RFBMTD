// Example 3 - Receiving binary data https://forum.arduino.cc/t/serial-input-basics-updated/382007/2
// More complete way to receive and parse arduino data.
// Start Transmission char: <
// End Transmission char: >

// Example 3 - Receive with start- and end-markers

// Defining LED lights to pinout

// Left: redL,yelL,grnL. Center: redM, yelM,grnM. Right: redR,yelR,grnR

// #define redM 4
// #define yelM 7
// #define yelL 8
// #define sts 9
// #define bat 10
// #define grnM 14
// #define grnL 15
// #define grnR 16
// #define redR 17
// #define redL 27
// #define yelR 28

// Intializing an array that receives chars 
const byte numChars = 32;
char receivedChars[numChars];

boolean newData = false;

void setup() {
    Serial.begin(9600);
    Serial.println("<Arduino is ready>");

    // Set LED pins as outputs 
    DDRD |= 0x90;
    DDRB |= 0x07;
    DDRC |= 0x3F;

    // Setup LEDS
    // pinMode(redL,OUTPUT);
    // pinMode(redM,OUTPUT);
    // pinMode(redR,OUTPUT);
    // pinMode(yelL,OUTPUT);
    // pinMode(yelM,OUTPUT);
    // pinMode(yelR,OUTPUT);
    // pinMode(grnL,OUTPUT);
    // pinMode(grnM,OUTPUT);
    // pinMode(grnR,OUTPUT);
    // pinMode(sts,OUTPUT);
    // pinMode(bat,OUTPUT);


    // Run a Lamp Check
    lampCheck();

    //Test the LED Lamps Individually
    controlCheck();  
}

void loop() {
    recvWithStartEndMarkers();
    showNewData();
    ledCntl();

    // Wait for serial input
    // Delete when ready
    while(Serial.available() == 0) {
    }

}

void allOff()
{
    // Turn off LEDs
    // digitalWrite(bat,  LOW);
    // digitalWrite(sts,  LOW);
    // digitalWrite(redL, LOW);
    // digitalWrite(redM, LOW);
    // digitalWrite(redR, LOW);
    // digitalWrite(yelL, LOW);
    // digitalWrite(yelM, LOW);
    // digitalWrite(yelR, LOW);
    // digitalWrite(grnL, LOW);
    // digitalWrite(grnM, LOW);
    // digitalWrite(grnR, LOW);
    PORTD &= 0x6F;
    PORTB &= 0xF8;
    PORTC &= 0xC0;
}

void allOn()
{
    // Turn on LEDs
    // digitalWrite(bat,  HIGH);
    // digitalWrite(sts,  HIGH);
    // digitalWrite(redL, HIGH);
    // digitalWrite(redM, HIGH);
    // digitalWrite(redR, HIGH);
    // digitalWrite(yelL, HIGH);
    // digitalWrite(yelM, HIGH);
    // digitalWrite(yelR, HIGH);
    // digitalWrite(grnL, HIGH);
    // digitalWrite(grnM, HIGH);
    // digitalWrite(grnR, HIGH);
    PORTD |= 0x90;
    PORTB |= 0x07;
    PORTC |= 0x3F;
}

// Send and receive communication scheme using "<" (start) & ">" (end)
void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;
 
    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}

void lampCheck() {

  /* SETUP */
  Serial.print("[Starting Setup] ");
  allOn();
  delay(1000); // delay for 3 sec
  allOff();

}

void controlCheck() {
  allOff();

// #define redM 4
// #define yelM 7
// #define yelL 8
// #define sts 9
// #define bat 10
// #define grnM 14
// #define grnL 15
// #define grnR 16
// #define redR 17
// #define redL 27
// #define yelR 28

  // Turn on LEDs
  // digitalWrite(redL, HIGH);
  PORTC |= 0x10;
  delay(1000); // delay for 1 sec
  // digitalWrite(redM, HIGH);
  PORTD |= 0x10;
  delay(1000); // delay for 1 sec
  // digitalWrite(redR, HIGH);
  PORTC |= 0x08;
  delay(1000); // delay for 1 sec
  // digitalWrite(yelR, HIGH);
  PORTC |= 0x20;
  delay(1000); // delay for 1 sec
  // digitalWrite(yelM, HIGH);
  PORTD |= 0x80;
  delay(1000); // delay for 1 sec
  // digitalWrite(yelL, HIGH);
  PORTB |= 0x01;
  delay(1000); // delay for 1 sec
  // digitalWrite(grnL, HIGH);
  PORTC |= 0x02;
  delay(1000); // delay for 1 sec
  // digitalWrite(grnM, HIGH);
  PORTC |= 0x01;
  delay(1000); // delay for 1 sec
  // digitalWrite(grnR, HIGH);
  PORTC |= 0x04;
  delay(1000); // delay for 1 sec
  // digitalWrite(bat,  HIGH);
  PORTB |= 0x04;
  delay(1000); // delay for 1 sec
  // digitalWrite(sts,  HIGH);
  PORTB |= 0x02;
  delay(1000); // delay for 1 sec

  allOff();
}

// Show receivedChars via serial monitor
void showNewData() {
    if (newData == true) {
        // Serial.print("R:");
        Serial.println(receivedChars);
        newData = false;
    }
}

void blink_num_times(char num_times, char pin_number) {
    // for loop based on N
    for(char x = 0; x < num_times; ++x) {
        //digitalWrite(bat, HIGH);
        PORTB |= 0x04;
        delay(1000); // 1 sec
        // digitalWrite(bat, LOW);
        PORTB &= 0xFB;
    }
}

// Control LEDs based on the receivedChars
void ledCntl()
{
  // L | C | R | S | B | Other Function
  // 0 | 1 | 2 | 3 | 4 | 5

  // L, C, R  => 0, 1, 2, 3     [0=off, 1=close, 2=med, 3=far]
  // S => 0, 1                  [0=off, 1=on]
  // B => 0, 1, 2, 3, 4         [0=off, 1 : < 25, 2 : >25,  3 : >50, 4 : >75]
  // Other Functions => TBD

  /* LEFT LEDs */
  if (receivedChars[0] == '0')
  {
    Serial.print("[Left OFF] ");
    // digitalWrite(redL, LOW);
    // digitalWrite(yelL, LOW);
    // digitalWrite(grnL, LOW);
    // PORTC |= 0x10;
    // PORTB |= 0x01;
    // PORTC |= 0x02;
    PORTC &= 0xEF;
    PORTB &= 0xFE;
    PORTC &= 0xFD;
  }

  else if (receivedChars[0] == '1')
  {
    Serial.print("[redL ON] ");
    // digitalWrite(redL, HIGH);
    // digitalWrite(yelL, LOW);
    // digitalWrite(grnL, LOW);
    PORTC |= 0x10;
    PORTC &= 0xFD;
    PORTC &= 0xEF;
  }

  else if (receivedChars[0] == '2')
  {
    Serial.print("[yelL ON] ");
    // digitalWrite(redL, LOW);
    // digitalWrite(yelL, HIGH);
    // digitalWrite(grnL, LOW);
    PORTC &= 0xEF;
    PORTB |= 0x01;
    PORTC &= 0xFD;

  }

  else if (receivedChars[0] == '3') 
  {
    Serial.print("[grnL ON] ");
    // digitalWrite(redL, LOW);
    // digitalWrite(yelL, LOW);
    // digitalWrite(grnL, HIGH);
    PORTC &= 0xEF;
    PORTB &= 0xFE;
    PORTC |= 0x02;    
  }

  else {;}  // do nothing

  /* CENTER LEDs */
  if (receivedChars[1] == '0')
  {
    Serial.print("[CENTER OFF] ");
    // digitalWrite(redM, LOW);
    // digitalWrite(yelM, LOW);
    // digitalWrite(grnM, LOW);
    // PORTD |= 0x10;
    // PORTD |= 0x80;
    // PORTC |= 0x01;
    PORTD &= 0x6F;
    PORTC &= 0xFE;
  }

  else if (receivedChars[1] == '1')
  {
    Serial.print("[redM ON] ");
    // digitalWrite(redM, HIGH);
    // digitalWrite(yelM, LOW);
    // digitalWrite(grnM, LOW);
    PORTD |= 0x10;
    PORTD &= 0x7F;
    PORTC &= 0xFE;
  }

  else if (receivedChars[1] == '2')
  {
    Serial.print("[yelM ON] ");
    // digitalWrite(redM, LOW);
    // digitalWrite(yelM, HIGH);
    // digitalWrite(grnM, LOW);
    PORTD &= 0xEF;
    PORTD |= 0x80;
    PORTC &= 0xFE;
  }

  else if (receivedChars[1] == '3') 
  {
    Serial.print("[grnM ON] ");
    // digitalWrite(redM, LOW);
    // digitalWrite(yelM, LOW);
    // digitalWrite(grnM, HIGH); 
    PORTD &= 0x6F;
    PORTC |= 0x01;   
  }

  else {;} // do nothing

  /* RIGHT LEDs */
  if (receivedChars[2] == '0')
  {
    Serial.print("[RIGHT OFF] ");
    // digitalWrite(redR, LOW);
    // digitalWrite(yelR, LOW);
    // digitalWrite(grnR, LOW);
    // PORTB |= 0x08;
    // PORTC |= 0x20;
    // PORTC |= 0x04;
    PORTB &= 0xF7;
    PORTC &= 0xDB;
  }

  else if (receivedChars[2] == '1')
  {
    Serial.print("[redR ON] ");
    // digitalWrite(redR, HIGH);
    // digitalWrite(yelR, LOW);
    // digitalWrite(grnR, LOW);
    PORTB |= 0x08;
    PORTC &= 0xDB;
  }

  else if (receivedChars[2] == '2')
  {
    Serial.print("[yelR ON] ");
    // digitalWrite(redR, LOW);
    // digitalWrite(yelR, HIGH);
    // digitalWrite(grnR, LOW);
    PORTB &= 0xF7;
    PORTC |= 0x20;
    PORTC &= 0xFB;
  }

  else if (receivedChars[2] == '3') 
  {
    Serial.print("[grnR ON] ");
    // digitalWrite(redR, LOW);
    // digitalWrite(yelR, LOW);
    // digitalWrite(grnR, HIGH); 
    PORTB &= 0xF7;
    PORTC &= 0xDF;
    PORTC |= 0x04;   
  }

  else {;} // do nothing

  /* STATUS LED */
  if(receivedChars[3] == '1') 
  {  
    Serial.print("[Status ON] ");
    // digitalWrite(sts, HIGH);
    PORTB |= 0x02;
  }

  else 
  {
    Serial.print("[Status OFF] ");
    // digitalWrite(sts, LOW);
    PORTB &= 0xFD;
  }

  /* BATTERY LED */
  if(receivedChars[4] == '4') 
  {
    Serial.print("[bat >75%] ");
    // blink_num_times(4, bat);

  } 
  
  else if (receivedChars[4] == '3') 
  {
    Serial.print("[bat >50%] ");
    // blink_num_times(3, bat);

  } 
  
  else if (receivedChars[4] == '2') 
  {
    Serial.print("[bat >25%] ");
    // blink_num_times(2, bat);

  } 
  
  else if (receivedChars[4] == '1')
  {
    Serial.print("[bat <25%] ");
    // blink_num_times(1, bat);
  }  

  else 
  {
    Serial.print("[bat OFF] ");
    // digitalWrite(bat, LOW);
    PORTB &= 0xFB;
  }

  // Other Functions if needed
  // if (receivedChars[5] == '1') {
  //   ;
  // }

}