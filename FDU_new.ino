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
  // LEFT LEDs
  if(receivedChars[0] == '1') 
  {
    Serial.print("[redL ON] ");
    // digitalWrite(redL, HIGH);

  } else {
    Serial.print("[redL OFF] ");
    // digitalWrite(redL, LOW);
  }

  if(receivedChars[1] == '1') 
  {
    Serial.print("[yelL ON] ");
    // digitalWrite(yelL, HIGH);

  } else {
    Serial.print("[yelL OFF] ");
    // digitalWrite(yelL, LOW);
  }

  if(receivedChars[2] == '1') 
  {
    Serial.print("[grnL ON] ");
    // digitalWrite(grnL, HIGH);

  } else {
    Serial.print("[grnL OFF] ");
    // digitalWrite(grnL, LOW);
  }

  // CENTER LEDs 
  if(receivedChars[3] == '1') 
  {
    Serial.print("[redM ON] ");
    // digitalWrite(redM, HIGH);

  } else {
    Serial.print("[redM OFF] ");
    // digitalWrite(redM, LOW);
  }

  if(receivedChars[4] == '1') 
  {
    Serial.print("[yelM ON] ");
    // digitalWrite(yelM, HIGH);

  } else {
    Serial.print("[yelM OFF] ");
    // digitalWrite(yelM, LOW);
  }  

  if(receivedChars[5] == '1') 
  {
    Serial.print("[grnM ON] ");
    // digitalWrite(grnM, HIGH);

  } else {
    Serial.print("[grnM OFF] ");
    // digitalWrite(grnM, LOW);
  }    

  // RIGHT LEDs
  if(receivedChars[6] == '1') 
  {
    Serial.print("[redR ON] ");
    // digitalWrite(redR, HIGH);

  } else {
    Serial.print("[redR OFF] ");
    // digitalWrite(redR, LOW);
  }    

  if(receivedChars[7] == '1') 
  {
    Serial.print("[yelR ON] ");
    // digitalWrite(yelR, HIGH);

  } else {
    Serial.print("[yelR OFF] ");
    // digitalWrite(yelR, LOW);
  }      

  if(receivedChars[8] == '1') 
  {
    Serial.print("[grnR ON] ");
    // digitalWrite(grnR, HIGH);

  } else {
    Serial.print("[grnR OFF] ");
    // digitalWrite(grnR, LOW);
  }  
  
  // STATUS LED [TODO: pwm?]
  if(receivedChars[9] == '1') 
  {
    Serial.print("[sts ON] ");
    // digitalWrite(sts, HIGH);

  } else {
    Serial.print("[sts OFF] ");
    // digitalWrite(sts, LOW);
  }            

  /*
    Should we only do a blink when the battery percentage changes?
      Changes past a threshold to take it a step further?
  */
  // BATTERY LED [TODO: pwm?]
  if(receivedChars[10] == '3') 
  {
    Serial.print("[bat >75%] ");
    blink_num_times(4, bat);

  } else if (receivedChars[10] == '2') {
    Serial.print("[bat >50%] ");
    blink_num_times(3, bat);

  } else if (receivedChars[10] == '1') {
    Serial.print("[bat >25%] ");
    blink_num_times(2, bat);

  } else {
    Serial.print("[bat <25%] ");
    blink_num_times(1, bat);
  }  

  // SETUP [blink 3 times]
  if(receivedChars[11] == '1') 
  {
      Serial.print("[Starting Setup] ");
      allOn();
      delay(1000);
      allOff();
      delay(1000);

      allOn();
      delay(1000);
      allOff();
      delay(1000);

      allOn();
      delay(1000);
      allOff();
      delay(1000);            
  } else {
      Serial.print("[Setup is OFF] ");

  }
}