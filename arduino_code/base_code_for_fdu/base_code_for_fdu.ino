// Example 6 - Receiving binary data
// More complete way to receive and parse arduino data.
// Start Transmission char: <
// End Transmission char: >
// Eric: We use this code just because it makes the transmission cleaniner to run. 

const byte numBytes = 32;
byte receivedBytes[numBytes];
byte numReceived = 0;

boolean newData = false;

void setup() {
    Serial.begin(9600);
    Serial.println("<Arduino is ready>");
}
// Add our stuff for the program here
void loop() {

// we do not need to consider the input buffer size of the arduino. It emptyies faster than it can be written. 
// also we can do execute ~900 instructions inbetween each read at a baud rate higher that 9600. So using 9600 we should not consider hang up between execution and serial communication.
  
    recvBytesWithStartEndMarkers();
    showNewData();
}

void recvBytesWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    byte startMarker = 0x3C; // < is (hex 3C, decimal 60)
    byte endMarker = 0x3E; // > is (hex 3E, decimal 62)
    byte rb;
   

    while (Serial.available() > 0 && newData == false) {
        rb = Serial.read();

        if (recvInProgress == true) {
            if (rb != endMarker) {
                receivedBytes[ndx] = rb;
                ndx++;
                if (ndx >= numBytes) {
                    ndx = numBytes - 1;
                }
            }
            else {
                receivedBytes[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                numReceived = ndx;  // save the number for use when printing
                ndx = 0;
                newData = true;
            }
        }

        else if (rb == startMarker) {
            recvInProgress = true;
        }
    }
}

void showNewData() {
    if (newData == true) {
        Serial.print("This is what I got...", char);
        for (byte n = 0; n < numReceived; n++) {
            Serial.print(receivedBytes[n]);
            Serial.print(' ');
        }
        Serial.println();
        newData = false;
    }
}
