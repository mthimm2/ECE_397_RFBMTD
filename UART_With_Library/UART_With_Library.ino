void setup() {
  
  Serial.begin(9600);
  while(!Serial);
  DDRD = 0x02;

}

void loop() {

  Serial.write(0x66);
  if(Serial.availableForWrite() == 1){
    
    Serial.flush();
    
  }

}
