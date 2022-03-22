// Example 3 - Receiving binary data https://forum.arduino.cc/t/serial-input-basics-updated/382007/2
// More complete way to receive and parse arduino data.
// Start Transmission char: <
// End Transmission char: >

// Example 3 - Receive with start- and end-markers

// Defining LED lights to pinout

// Left: redL,yelL,grnL. Center: redM, yelM,grnM. Right: redR,yelR,grnR

#define redL 6 
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
  // 00 = off, 01 = far, 10 = med, 11 = close
  // LL | CC | RR | SB
  // 01 | 23 | 45 | 67

  /* LEFT LEDs */
  if (receivedChars[0] == '1' and receivedChars[1] == "1")
  {
    Serial.print("[redL ON] ");
    // digitalWrite(redL, HIGH);
    // digitalWrite(yelL, LOW);
    // digitalWrite(grnL, LOW);
  }

  else if (receivedChars[0] == '1' and receivedChars[1] == "0")
  {
    Serial.print("[yelL ON] ");
    // digitalWrite(redL, LOW);
    // digitalWrite(yelL, HIGH);
    // digitalWrite(grnL, LOW);
  }

  else if (receivedChars[0] == '0' and receivedChars[1] == "1")
  {
    Serial.print("[grnL ON] ");
    // digitalWrite(redL, LOW);
    // digitalWrite(yelL, LOW);
    // digitalWrite(grnL, HIGH);
  }

  else if (receivedChars[0] == '0' and receivedChars[1] == "0") 
  {
    Serial.print("[Left OFF] ");
    // digitalWrite(redL, LOW);
    // digitalWrite(yelL, LOW);
    // digitalWrite(grnL, LOW);    
  }

  else {;}  // do nothing

  /* CENTER LEDs */
  if (receivedChars[2] == '1' and receivedChars[3] == "1")
  {
    Serial.print("[redL ON] ");
    // digitalWrite(redL, HIGH);
    // digitalWrite(yelL, LOW);
    // digitalWrite(grnL, LOW);
  }

  else if (receivedChars[2] == '1' and receivedChars[3] == "0")
  {
    Serial.print("[yelM ON] ");
    // digitalWrite(redM, LOW);
    // digitalWrite(yelM, HIGH);
    // digitalWrite(grnM, LOW);
  }

  else if (receivedChars[2] == '0' and receivedChars[3] == "1")
  {
    Serial.print("[grnM ON] ");
    // digitalWrite(redM, LOW);
    // digitalWrite(yelM, LOW);
    // digitalWrite(grnM, HIGH);
  }

  else if (receivedChars[2] == '0' and receivedChars[3] == "0") 
  {
    Serial.print("[Center OFF] ");
    // digitalWrite(redM, LOW);
    // digitalWrite(yelM, LOW);
    // digitalWrite(grnM, LOW);    
  }

  else {;} // do nothing

  /* RIGHT LEDs */
  if (receivedChars[4] == '1' and receivedChars[5] == "1")
  {
    Serial.print("[redR ON] ");
    // digitalWrite(redR, HIGH);
    // digitalWrite(yelR, LOW);
    // digitalWrite(grnR, LOW);
  }

  else if (receivedChars[4] == '1' and receivedChars[5] == "0")
  {
    Serial.print("[yelM ON] ");
    // digitalWrite(redR, LOW);
    // digitalWrite(yelR, HIGH);
    // digitalWrite(grnR, LOW);
  }

  else if (receivedChars[4] == '0' and receivedChars[5] == "1")
  {
    Serial.print("[grnM ON] ");
    // digitalWrite(redR, LOW);
    // digitalWrite(yelR, LOW);
    // digitalWrite(grnR, HIGH);
  }

  // 00
  else if (receivedChars[4] == '0' and receivedChars[5] == "0") 
  {
    Serial.print("[Center OFF] ");
    // digitalWrite(redR, LOW);
    // digitalWrite(yelR, LOW);
    // digitalWrite(grnR, LOW);    
  }

  else {;} // do nothing

  /* STATUS LED */
  if(receivedChars[6] == '1') 
  {  
    Serial.print("[Status ON] ");
    // digitalWrite(sts, HIGH);
  }

  else 
  {
    Serial.print("[Status OFF] ");
    // digitalWrite(sts, LOW);
  }

  /* BATTERY LED */
  if(receivedChars[7] == '3') 
  {
    Serial.print("[bat >75%] ");
    blink_num_times(4, bat);

  } 
  
  else if (receivedChars[7] == '2') 
  {
    Serial.print("[bat >50%] ");
    blink_num_times(3, bat);

  } 
  
  else if (receivedChars[7] == '1') 
  {
    Serial.print("[bat >25%] ");
    blink_num_times(2, bat);

  } 
  
  else 
  {
    Serial.print("[bat <25%] ");
    blink_num_times(1, bat);
  }  


  /* SETUP */
  if(receivedChars[0] = '1' && receivedChars[1] = '1' && receivedChars[2] = '1' && receivedChars[3] = '1' && receivedChars[4] = '1' && receivedChars[5] = '1' && receivedChars[6] = '1' && receivedChars[7] = '1') 
  {
      Serial.print("[Starting Setup] ");
      allOn();
      delay(3000); // delay for 3 sec
      allOff();

  } else {
      Serial.print("[Setup is OFF] ");

  }


}