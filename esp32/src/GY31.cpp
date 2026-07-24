#include <Arduino.h>
#include <driver/i2s.h>

#define S0 6
#define S1 5
#define S2 3
#define S3 4
#define sensorOut 2
#define LED_PIN 7

int R, G, B;

void setup() {
  pinMode(S0, OUTPUT);
  pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT);
  pinMode(S3, OUTPUT);
  pinMode(sensorOut, INPUT);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  digitalWrite(S0, HIGH);
  digitalWrite(S1, LOW);

  Serial.begin(115200);
}

int readRed() {
  digitalWrite(S2, LOW);
  digitalWrite(S3, LOW);
  return pulseIn(sensorOut, LOW);
}

int readGreen() {
  digitalWrite(S2, HIGH);
  digitalWrite(S3, HIGH);
  return pulseIn(sensorOut, LOW);
}

int readBlue() {
  digitalWrite(S2, LOW);
  digitalWrite(S3, HIGH);
  return pulseIn(sensorOut, LOW);
}

void loop() {

    if (Serial.available()){
        String cmd = Serial.readStringUntil("\n");
        cmd.trim();

        if ( cmd == "D"){
            R = readRed();
            G = readGreen();
            B = readBlue();


            Serial.print("R=");
            Serial.print(R);
            Serial.print(" G=");
            Serial.print(G);
            Serial.print(" B=");
            Serial.print(B);
            Serial.print(" --> ");

            // Giá trị nhỏ hơn = màu mạnh hơn

            if(R < G && R < B){
                if(abs(G-B)<40)
                    Serial.println("RED");
                else if(G < B)
                    Serial.println("ORANGE");
                else
                    Serial.println("PINK");
            }

            else if(G < R && G < B){
                if(abs(R-B)<40)
                    Serial.println("GREEN");
                else if(R < B)
                    Serial.println("YELLOW");
                else
                    Serial.println("LIME");
            }

            else if(B < R && B < G){
                if(abs(R-G)<40)
                    Serial.println("BLUE");
                else if(R < G)
                    Serial.println("PURPLE");
                else
                    Serial.println("CYAN");
            }

            else if(abs(R-G)<25 && abs(G-B)<25){
                if(R<250)
                    Serial.println("WHITE");
                else if(R<450)
                    Serial.println("GRAY");
                else
                    Serial.println("BLACK");
            }

            else{
                Serial.println("UNKNOWN");
            }

            delay(300);
        }
    }
}