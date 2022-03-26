// Example 3 - Receiving binary data https://forum.arduino.cc/t/serial-input-basics-updated/382007/2
// More complete way to receive and parse arduino data.
// Start Transmission char: <
// End Transmission char: >

// Example 3 - Receive with start- and end-markers

// Defining LED lights to pinout

// Left: redL,yelL,grnL. Center: redM, yelM,grnM. Right: redR,yelR,grnR

#define redL 18
#define redM 4
#define redR 17
#define yelL 8
#define yelM 7
#define yelR 19
#define grnL 15
#define grnM 14
#define grnR 16
#define sts 9
#define bat 10

// Intializing an array that receives chars 
const byte numChars = 32;
char receivedChars[numChars];

boolean newData = false;

void setup() {
    Serial.begin(9600);
    Serial.println("<Arduino is ready>");

    // Setup LEDS
    pinMode(redL,OUTPUT);
    pinMode(redM,OUTPUT);
    pinMode(redR,OUTPUT);
    pinMode(yelL,OUTPUT);
    pinMode(yelM,OUTPUT);
    pinMode(yelR,OUTPUT);
    pinMode(grnL,OUTPUT);
    pinMode(grnM,OUTPUT);
    pinMode(grnR,OUTPUT);
    pinMode(sts,OUTPUT);
    pinMode(bat,OUTPUT);  

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
    digitalWrite(bat,  LOW);
    digitalWrite(sts,  LOW);
    digitalWrite(redL, LOW);
    digitalWrite(redM, LOW);
    digitalWrite(redR, LOW);
    digitalWrite(yelL, LOW);
    digitalWrite(yelM, LOW);
    digitalWrite(yelR, LOW);
    digitalWrite(grnL, LOW);
    digitalWrite(grnM, LOW);
    digitalWrite(grnR, LOW);
}

void allOn()
{
    // Turn on LEDs
    digitalWrite(bat,  HIGH);
    digitalWrite(sts,  HIGH);
    digitalWrite(redL, HIGH);
    digitalWrite(redM, HIGH);
    digitalWrite(redR, HIGH);
    digitalWrite(yelL, HIGH);
    digitalWrite(yelM, HIGH);
    digitalWrite(yelR, HIGH);
    digitalWrite(grnL, HIGH);
    digitalWrite(grnM, HIGH);
    digitalWrite(grnR, HIGH);
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
  if(receivedChars[0] == '1' && receivedChars[1] == '1' && receivedChars[2] == '1' && receivedChars[3] == '1' && receivedChars[4] == '1' && receivedChars[5] == '1' && receivedChars[6] == '1' && receivedChars[7] == '1') 
  {
      Serial.print("[Starting Setup] ");
      allOn();
      delay(3000); // delay for 3 sec
      allOff();

  } 
  
  else {
      Serial.print("[Setup is OFF] ");

  }
}

void controlCheck() {
  allOff();

  // Turn on LEDs
  digitalWrite(redL, HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(redM, HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(redR, HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(yelR, HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(yelM, HIGH);
  delay(1000); // delay for 1 sec

  digitalWrite(yelL, HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(grnL, HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(grnM, HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(grnR, HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(bat,  HIGH);
  delay(1000); // delay for 1 sec
  digitalWrite(sts,  HIGH);
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
        digitalWrite(bat, HIGH);
        delay(1000); // 1 sec
        digitalWrite(bat, LOW);
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
    digitalWrite(redL, LOW);
    digitalWrite(yelL, LOW);
    digitalWrite(grnL, LOW);
  }

  else if (receivedChars[0] == '1')
  {
    Serial.print("[redL ON] ");
    digitalWrite(redL, HIGH);
    digitalWrite(yelL, LOW);
    digitalWrite(grnL, LOW);
  }

  else if (receivedChars[0] == '2')
  {
    Serial.print("[yelL ON] ");
    digitalWrite(redL, LOW);
    digitalWrite(yelL, HIGH);
    digitalWrite(grnL, LOW);
  }

  else if (receivedChars[0] == '3') 
  {
    Serial.print("[grnL ON] ");
    digitalWrite(redL, LOW);
    digitalWrite(yelL, LOW);
    digitalWrite(grnL, HIGH);    
  }

  else {;}  // do nothing

  /* CENTER LEDs */
  if (receivedChars[1] == '0')
  {
    Serial.print("[CENTER OFF] ");
    digitalWrite(redM, LOW);
    digitalWrite(yelM, LOW);
    digitalWrite(grnM, LOW);
  }

  else if (receivedChars[1] == '1')
  {
    Serial.print("[redM ON] ");
    digitalWrite(redM, HIGH);
    digitalWrite(yelM, LOW);
    digitalWrite(grnM, LOW);
  }

  else if (receivedChars[1] == '2')
  {
    Serial.print("[yelM ON] ");
    digitalWrite(redM, LOW);
    digitalWrite(yelM, HIGH);
    digitalWrite(grnM, LOW);
  }

  else if (receivedChars[1] == '3') 
  {
    Serial.print("[grnM ON] ");
    digitalWrite(redM, LOW);
    digitalWrite(yelM, LOW);
    digitalWrite(grnM, HIGH);    
  }

  else {;} // do nothing

  /* RIGHT LEDs */
  if (receivedChars[2] == '0')
  {
    Serial.print("[RIGHT OFF] ");
    digitalWrite(redR, LOW);
    digitalWrite(yelR, LOW);
    digitalWrite(grnR, LOW);
  }

  else if (receivedChars[2] == '1')
  {
    Serial.print("[redR ON] ");
    digitalWrite(redR, HIGH);
    digitalWrite(yelR, LOW);
    digitalWrite(grnR, LOW);
  }

  else if (receivedChars[2] == '2')
  {
    Serial.print("[yelR ON] ");
    digitalWrite(redR, LOW);
    digitalWrite(yelR, HIGH);
    digitalWrite(grnR, LOW);
  }

  else if (receivedChars[2] == '3') 
  {
    Serial.print("[grnR ON] ");
    digitalWrite(redR, LOW);
    digitalWrite(yelR, LOW);
    digitalWrite(grnR, HIGH);    
  }

  else {;} // do nothing

  /* STATUS LED */
  if(receivedChars[3] == '1') 
  {  
    Serial.print("[Status ON] ");
    digitalWrite(sts, HIGH);
  }

  else 
  {
    Serial.print("[Status OFF] ");
    digitalWrite(sts, LOW);
  }

  /* BATTERY LED */
  if(receivedChars[4] == '4') 
  {
    Serial.print("[bat >75%] ");
    blink_num_times(4, bat);

  } 
  
  else if (receivedChars[4] == '3') 
  {
    Serial.print("[bat >50%] ");
    blink_num_times(3, bat);

  } 
  
  else if (receivedChars[4] == '2') 
  {
    Serial.print("[bat >25%] ");
    blink_num_times(2, bat);

  } 
  
  else if (receivedChars[4] == '1')
  {
    Serial.print("[bat <25%] ");
    blink_num_times(1, bat);
  }  

  else 
  {
    Serial.print("[bat OFF] ");
    digitalWrite(bat, LOW);
  }

  // Other Functions if needed
  // if (receivedChars[5] == '1') {
  //   ;
  // }

}