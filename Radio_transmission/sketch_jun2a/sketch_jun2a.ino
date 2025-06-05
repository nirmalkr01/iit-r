#include <SoftwareSerial.h>
#include <ESP8266WiFi.h>

SoftwareSerial mySerial(D2, D1); // RX, TX

const int ledPin = 2; // GPIO 2 (D4 on NodeMCU)
unsigned long lastReceivedTime = 0;
const long timeout = 3000; // 3 seconds timeout

void setup() {
  Serial.begin(9600);
  delay(2000); // Wait for Serial to initialize
  Serial.println("Starting receiver setup...");

  // Disable WiFi to reduce SoftwareSerial interference
  WiFi.mode(WIFI_OFF);

  mySerial.begin(9600);
  pinMode(D5, OUTPUT); // M0
  pinMode(D6, OUTPUT); // M1
  pinMode(ledPin, OUTPUT); // LED pin
  digitalWrite(ledPin, LOW); // LED off initially
  
  // Set to configuration mode (M0 = 1, M1 = 1)
  digitalWrite(D5, HIGH);
  digitalWrite(D6, HIGH);
  delay(1000);
  Serial.println("Entered configuration mode");

  // Configure module: Address 0x0000, 9600 baud, 2.4kbps, 915 MHz (CHAN 0x17), 30dBm
  byte config[] = {0xC0, 0x00, 0x00, 0x1A, 0x17, 0x00}; // HEAD, ADDH, ADDL, SPED, CHAN, OPTION
  mySerial.write(config, 6);
  delay(1000);
  Serial.println("Configuration sent");

  // Read configuration to verify
  byte readCmd[] = {0xC1, 0xC1, 0xC1};
  mySerial.write(readCmd, 3);
  delay(100);
  Serial.print("Configuration response: ");
  while (mySerial.available()) {
    Serial.print("0x");
    Serial.print(mySerial.read(), HEX);
    Serial.print(" ");
  }
  Serial.println();

  // Switch to normal mode (M0 = 0, M1 = 0)
  digitalWrite(D5, LOW);
  digitalWrite(D6, LOW);
  delay(1000);
  Serial.println("Receiver ready (normal mode)");

  // Blink LED to confirm setup
  digitalWrite(ledPin, HIGH);
  delay(500);
  digitalWrite(ledPin, LOW);
  delay(500);
  digitalWrite(ledPin, HIGH);
  delay(500);
  digitalWrite(ledPin, LOW);
}

void loop() {
  static char buffer[32];
  static int index = 0;

  // Read incoming bytes
  while (mySerial.available() > 0) {
    char c = mySerial.read();
    Serial.print("Received byte: 0x");
    Serial.print(c, HEX);
    Serial.println();
    
    buffer[index] = c;
    index++;

    // Prevent buffer overflow
    if (index >= 32) {
      index = 0;
      Serial.println("Buffer overflow, resetting");
    }

    // Check if we have at least 8 bytes (3 for ADDH/ADDL/CHAN + 5 for "hello")
    if (index >= 8) {
      // Verify address (0x00, 0x00) and channel (0x17)
      if (buffer[0] == 0x00 && buffer[1] == 0x00 && buffer[2] == 0x17) {
        // Check if message is "hello"
        if (buffer[3] == 'h' && buffer[4] == 'e' && buffer[5] == 'l' && 
            buffer[6] == 'l' && buffer[7] == 'o') {
          Serial.println("Received: hello");
          digitalWrite(ledPin, HIGH); // Turn LED ON
          lastReceivedTime = millis(); // Update last received time
        }
      }
      index = 0; // Reset buffer
    }
  }

  // Turn LED OFF if no message received within timeout
  if (millis() - lastReceivedTime > timeout && lastReceivedTime != 0) {
    digitalWrite(ledPin, LOW); // Turn LED OFF
  }
}