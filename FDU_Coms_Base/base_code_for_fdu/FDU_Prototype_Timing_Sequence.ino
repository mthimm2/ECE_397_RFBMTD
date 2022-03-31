// Example 3 - Receiving binary data https://forum.arduino.cc/t/serial-input-basics-updated/382007/2
// More complete way to receive and parse arduino data.
// Start Transmission char: <
// End Transmission char: >

// Example 3 - Receive with start- and end-markers

// Defining LED lights to pinout

// Left: redL,yelL,grnL. Center: redM, yelM,grnM. Right: redR,yelR,grnR

#define redM 4
#define yelM 7
#define yelL 8
#define sts 9
#define bat 10
#define grnM 14
#define grnL 15
#define grnR 16
#define redR 17
#define redL 27
#define yelR 28

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

  // Turn off all LEDs
  allOff();

}

void loop() {
  
  /*
    All delay times used are based on bringing the clips into editing software and looking at the fine-grained timing of stuff.
  */
  // passing25To40();
  // passing220To230();
  // passing242To252();
  // roundabout_15_to_45();  
}

/*
  For use with Passing.mp4
  0:25 - 0:40
*/
void passing25To40() {

  // Car starts off ~Medium distance away at 0:25
  digitalWrite(yelM, HIGH);

  // BB gets noticably smaller, so I'll shift to the green center light
  delay(3540);
  allOff();
  digitalWrite(grnM, HIGH);

  // Then, for the remainder of the video, we stay far away.
  // Note that delays add to 15s
  delay(116460);
  allOff();

}

/*
  For use with Passing.mp4
  2:20 - 2:30
*/
void passing220To230() {

  // Car starts in the center section of the frame at a medium distance
  digitalWrite(yelM, HIGH);

  // A red car enters frame from the right and has a big BB
  // Car in the middle stays there at about the same distance
  delay(2510);
  digitalWrite(redL, HIGH);
  
  // At around 2:24, I'd say that the center car's BB is big enough to probably be "close"
  delay(970);
  allOff();
  digitalWrite(redM, HIGH);

  // Shortly thereafter, the red car appears in the center segment, but isn't closer than the original car

  // At ~2:25.5, the original car enters the right segment, leaving the red car far away in the center
  delay(2270);
  allOff();
  digitalWrite(redL, HIGH);
  digitalWrite(grnM, HIGH);

  // Very shortly thereafter, the red car moves into the left segment
  delay(700);
  allOff();
  digitalWrite(redL, HIGH);
  digitalWrite(grnR, HIGH);

  // At 2:27, the original car starts to go undetected as it passes on the right.
  // The BB flickers a bit, so I've tried to replicate that with the delays
  delay(800);
  digitalWrite(redL, LOW);
  delay(150);
  digitalWrite(redL, HIGH);
  delay(60);
  digitalWrite(redL, LOW);
  delay(30);
  digitalWrite(redL, HIGH);
  delay(300);

  // Wait until clip end
  delay(2210);

  // After that, no more cars are in frame.
  allOff();
}

void passing242To252() {

  // At ~2:41.6, we pick up a car on the far right of the frame
  delay(1630);
  digitalWrite(grnL, HIGH);

  // We lose tracking for just a moment
  delay(60);
  digitalWrite(grnL, LOW);

  // Then we pick up the right cluster of cars
  // is detected
  delay(760);
  digitalWrite(grnL, HIGH);

  // One far car moves into the center segment and right segment still has cars too
  delay(1210);
  digitalWrite(grnM, HIGH);

  // Then the close car enters frame at about 2:36
  delay(340);
  digitalWrite(grnL, LOW);
  digitalWrite(redL, HIGH);

  // Maybe 1 second later, the close car starts to pull away, moving to a medium distance.
  // Far cars in the center segment are still picked up.
  delay(1180);
  allOff();
  digitalWrite(grnM, HIGH);
  digitalWrite(yelL, HIGH);

  // Finally, the close car pulls away to the right of the frame and is far away. Little cars still getting picked up in the center.
  delay(2330);
  allOff();
  digitalWrite(grnL, HIGH);
  digitalWrite(grnM, HIGH);

  // Little car on the left gets picked up
  delay(180);
  digitalWrite(grnR, HIGH);

  // Close car gets lost for a moment
  delay(60);
  digitalWrite(grnL, LOW);

  // Reappears
  delay(30);
  digitalWrite(grnL, HIGH);

  // Far left car is lost and close car is lost again
  delay(90);
  digitalWrite(grnR, LOW);
  digitalWrite(grnL, LOW);

  // Far left car reappears
  delay(60);
  digitalWrite(grnR, HIGH);

  // Close car reappears
  delay(180);
  digitalWrite(grnL, HIGH);

  // Middle car flickers
  delay(120);
  digitalWrite(grnM, LOW);

  // Reappears
  delay(30);
  digitalWrite(grnM, HIGH);

  // Middle disappears
  delay(30);
  digitalWrite(grnM, LOW);

  // New far middle car
  delay(450);
  digitalWrite(grnM, HIGH);

  // New center car flickers
  delay(120);
  digitalWrite(grnM, LOW);

  // Reappears
  delay(30);
  digitalWrite(grnM, HIGH);

  // New center car flickers
  delay(210);
  digitalWrite(grnM, LOW);

  // Reappears
  delay(30);
  digitalWrite(grnM, HIGH);

  // Left segment goes vacant
  delay(330);
  digitalWrite(grnR, LOW);

  // Wait until clip end
  delay(540);
  allOff();

}

void roundabout_15_to_45() {

  // Right from the start we have stuff in every segment at a far distance
  digitalWrite(grnR, HIGH);
  digitalWrite(grnM, HIGH);
  digitalWrite(grnL, HIGH);

  // Then, we block the cars on the left
  delay(1930);
  digitalWrite(grnR, LOW);

  // Then, Omar flexes and his sedan becomes visible close on the left of the frame
  delay(2240);
  digitalWrite(redR, HIGH);

  // Shortly thereafter we lose sight of omar's car due to the bike in front of it. The center segment also goes vacant
  delay(430);
  digitalWrite(redR, LOW);
  digitalWrite(grnM, LOW);

  // Omar's sedan pops back up on the left of the frame
  delay(130);
  digitalWrite(redR, HIGH);

  // A couple of flickers of Omar's wheels
  delay(30);
  digitalWrite(redR, LOW);
  delay(30);
  digitalWrite(redR, HIGH);
  delay(30);
  digitalWrite(redR, LOW);
  delay(30);
  digitalWrite(redR, HIGH);
  delay(30);
  digitalWrite(redR, LOW);
  delay(30);
  digitalWrite(redR, HIGH);
  delay(30);
  digitalWrite(redR, LOW);
  delay(60);
  digitalWrite(redR, HIGH);
  delay(30);
  digitalWrite(redR, LOW);
  delay(90);
  digitalWrite(redR, HIGH);
  delay(30);
  digitalWrite(redR, LOW);
  delay(180);
  digitalWrite(redR, HIGH);

  // Jim's car reappears in center, but Omar's car is now in center and is closer
  delay(830);
  digitalWrite(redR, LOW);
  digitalWrite(redM, HIGH);

  // Omar's car heads back to the left segment
  delay(1430);
  digitalWrite(redM, LOW);
  digitalWrite(redR, HIGH);

  // Silver honda fit slips into center
  delay(270);
  digitalWrite(grnM, HIGH);

  // Omar's car is getting farther and Eric's bumper is now in view.
  delay(2800);
  digitalWrite(redR, LOW);
  digitalWrite(yelR, HIGH);

  // Omar's car goes to center
  delay(330);
  digitalWrite(yelR, LOW);
  digitalWrite(grnM, LOW);
  digitalWrite(yelM, HIGH);
  
  // My car slips in on the left
  delay(300);
  digitalWrite(redR, HIGH);

  // My car flickers
  delay(60);
  digitalWrite(redR, LOW);
  delay(100);
  digitalWrite(redR, HIGH);

  // Another flicker
  delay(30);
  digitalWrite(redR, LOW);
  delay(200);
  digitalWrite(redR, HIGH);

  // Black passing on right and Omar's car is now far away
  delay(730);
  allOff();
  digitalWrite(redL, HIGH);
  digitalWrite(grnM, HIGH);
  digitalWrite(redR, HIGH);

  // Black chevy is lost, but still cars in right segment far away
  delay(600);
  digitalWrite(redL, LOW);
  digitalWrite(grnL, HIGH);

  // My car goes into center segment
  delay(1060);
  digitalWrite(redR, LOW);
  digitalWrite(grnM, LOW);
  digitalWrite(redM, HIGH);

  // Black Nissan comes into view on left
  delay(4730);
  digitalWrite(redR, HIGH);

  // Black Toyota not yet recognized and Nissan goes to center segment
  delay(3600);
  digitalWrite(redR, LOW);

  // My car slips into the right segment and is wide in profile, so this would probably be a "close detection"
  delay(630);
  digitalWrite(grnL, LOW);
  digitalWrite(redL, HIGH);

  // My car slips back into center
  delay(300);
  digitalWrite(redL, LOW);
  digitalWrite(grnL, HIGH);

  // My car slips back to right of frame
  delay(530);
  digitalWrite(redL, HIGH);
  digitalWrite(grnL, LOW);

  // My car finally slims out on the right
  delay(1470);
  digitalWrite(redL, LOW);
  digitalWrite(yelL, HIGH);

  // Black Toyota goes to center and Jeep is picked up on the left
  delay(10000)
  digitalWrite(redR, HIGH);

  // Jeep slips to center, then scene stays the same until end
  delay(170)
  digitalWrite(redR, LOW);

  // Until end
  delay(77);
  allOff();

}

void jimsCMFLCRDemo() {

  // All close LEDs on
  digitalWrite(redL, HIGH);
  digitalWrite(redM, HIGH);
  digitalWrite(redR, HIGH);

  // All medium LEDs on
  delay(250);
  allOff();
  digitalWrite(yelL, HIGH);
  digitalWrite(yelM, HIGH);  
  digitalWrite(yelR, HIGH);

  // All far LEDs on
  delay(250);
  allOff();
  digitalWrite(grnL, HIGH);
  digitalWrite(grnM, HIGH);
  digitalWrite(grnR, HIGH);

  // Left column on
  delay(250);
  allOff();
  digitalWrite(redL, HIGH);
  digitalWrite(yelL, HIGH);
  digitalWrite(grnL, HIGH);

  // Middle column on
  delay(250);
  allOff();
  digitalWrite(redM, HIGH);
  digitalWrite(yelM, HIGH);
  digitalWrite(grnM, HIGH);

  // Right column on
  delay(250);
  allOff();
  digitalWrite(redR, HIGH);
  digitalWrite(yelR, HIGH);
  digitalWrite(grnR, HIGH);

  delay(250);
  allOff();

}

void allOff() {
  digitalWrite(redL,LOW);
  digitalWrite(redM,LOW);
  digitalWrite(redR,LOW);
  digitalWrite(yelL,LOW);
  digitalWrite(yelM,LOW);
  digitalWrite(yelR,LOW);
  digitalWrite(grnL,LOW);
  digitalWrite(grnM,LOW);
  digitalWrite(grnR,LOW);
  digitalWrite(sts,LOW);
  digitalWrite(bat,LOW);
}