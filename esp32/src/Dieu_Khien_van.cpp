#include <Arduino.h>

#define RELAY_PIN 7

// Đổi thành false nếu relay của bạn Active HIGH
const bool ACTIVE_LOW = true;

void relayOn() {
  digitalWrite(RELAY_PIN, ACTIVE_LOW ? HIGH : LOW);
}

void relayOff() {
  digitalWrite(RELAY_PIN, ACTIVE_LOW ? LOW : HIGH);
}

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);
  relayOff();   // Ban đầu tắt van

  Serial.println("ESP32 Ready");
}

void loop() {

  if (Serial.available()) {

    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "ON") {
      relayOn();
      Serial.println("VALVE ON");
    }

    else if (cmd == "OFF") {
      relayOff();
      Serial.println("VALVE OFF");
    }
  }
}