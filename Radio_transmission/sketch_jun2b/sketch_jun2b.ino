#include <SoftwareSerial.h>
#include <ESP8266WiFi.h>

SoftwareSerial mySerial(D2, D1); // RX, TX

void setup() {
  Serial.begin(9600);
  delay(2000); // Wait for Serial to initialize
  Serial.println("Starting transmitter setup...");

  // Disable WiFi to reduce SoftwareSerial interference
  WiFi.mode(WIFI_OFF);

  mySerial.begin(9600);
  pinMode(D5, OUTPUT); // M0
  pinMode(D6, OUTPUT); // M1
  
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
  Serial.println("Transmitter ready (normal mode)");
}

void loop() {
  // Send message "hello" to address 0x0000, channel 0x17
  byte message[] = {0x00, 0x00, 0x17, 'h', 'e', 'l', 'l', 'o'};
  mySerial.write(message, 8); // 3 bytes (ADDH, ADDL, CHAN) + 5 bytes ("hello")
  Serial.println("Sent: hello");
  delay(2000); // Send every 2 seconds
}