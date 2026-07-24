#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define trig 2
#define echo 3
void setup() {
  Serial.begin(115200);
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);
}
void loop() {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  long duration = pulseIn(echo, HIGH);
  float distance = duration * 0.0343 / 2 ;

  Serial.println(distance);
  Serial.println(" cm");
  delay(500);
}
 