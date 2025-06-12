const int gasAnalogPin = A0;    // Analog pin for gas sensor
const int gasDigitalPin = D4;   // D4 (GPIO2) for gas sensor digital output
const int bulbPin = D2;         // D2 (GPIO4) for bulb

void setup() {
  // Initialize Serial Monitor
  Serial.begin(9600);
  // Set gas digital pin as input
  pinMode(gasDigitalPin, INPUT);
  // Set bulb pin as output
  pinMode(bulbPin, OUTPUT);
  // Ensure bulb is off initially
  digitalWrite(bulbPin, LOW);
}

void loop() {
  // Read gas sensor
  int gasAnalogValue = analogRead(gasAnalogPin);
  int gasDigitalValue = digitalRead(gasDigitalPin);
  
  // Print gas sensor status
  Serial.print("Gas Level (Analog): ");
  Serial.print(gasAnalogValue);
  Serial.println("/1023");
  if (gasDigitalValue == HIGH) {
    Serial.println("Status: Gas Detected!");
    digitalWrite(bulbPin, HIGH); // Turn bulb on if gas detected
  } else {
    Serial.println("Status: No Gas");
    digitalWrite(bulbPin, LOW);  // Turn bulb off if no gas
  }
  
  // Wait 2 seconds
  delay(2000);
}