#include <Arduino.h>
#include <driver/i2s.h>

//========================
// Relay
//========================
#define RELAY_PIN 7
const bool ACTIVE_LOW = true;

//========================
// I2S
//========================
#define I2S_PORT I2S_NUM_0

#define I2S_WS   10
#define I2S_SCK  11
#define I2S_SD   9

#define SAMPLE_RATE 16000

//========================
// Thời gian thu tối đa
// (Python sẽ gửi thời gian thực tế)
//========================

#define MAX_RECORD_TIME 3000    // ms
const int MAX_SAMPLE = SAMPLE_RATE * MAX_RECORD_TIME / 1000;
int16_t audioBuffer[MAX_SAMPLE];
bool state = true;
//========================

void setup() {

  Serial.begin(921600);

  // Relay OFF
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, ACTIVE_LOW ? LOW : HIGH);

  //========================
  // Cấu hình I2S
  //========================

  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 256,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  if (i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL) != ESP_OK) {
    Serial.println("I2S Driver Install Failed!");
    while (1);
  }

  if (i2s_set_pin(I2S_PORT, &pin_config) != ESP_OK) {
    Serial.println("I2S Pin Config Failed!");
    while (1);
  }

  Serial.println("READY");
}

void loop() {

  if (Serial.available()) {;
    // Nhận lệnh: ON,50,750
    String line = Serial.readStringUntil('\n');
    line.trim();

    int comma1 = line.indexOf(',');
    int comma2 = line.indexOf(',', comma1 + 1);
    int relayTime = 0;
    int recordTime = 0;
    String cmd = line.substring(0, comma1);
    if (comma1 != -1){
      relayTime = line.substring(comma1 + 1, comma2).toInt();
    }
    if (comma2 != -1) {
      recordTime = line.substring(comma2 + 1).toInt();
    }
    if (cmd == "ON") {
      
      // Không cho vượt quá bộ nhớ đã cấp phát
      if (recordTime > MAX_RECORD_TIME)
        recordTime = MAX_RECORD_TIME;

      //------------------------
      // Mở van
      //------------------------

      digitalWrite(RELAY_PIN, ACTIVE_LOW ? HIGH : LOW);
      delay(relayTime);
      digitalWrite(RELAY_PIN, ACTIVE_LOW ? LOW : HIGH);

      unsigned long startTime = millis();
      int sampleCount = 0;
      int32_t sample;
      size_t bytesRead;

      while (millis() - startTime < recordTime) {

        if (i2s_read(I2S_PORT,
                    &sample,
                    sizeof(sample),
                    &bytesRead,
                    portMAX_DELAY) == ESP_OK &&
            bytesRead == sizeof(sample)) {
          sample >>= 8;
          audioBuffer[sampleCount++] = (int16_t)(sample >> 8);
          if (sampleCount >= MAX_SAMPLE)
            break;
        }
      }
      Serial.println("DATA_BEGIN");
      Serial.write((uint8_t *)&sampleCount, sizeof(sampleCount));
      Serial.write((uint8_t *)audioBuffer,sampleCount * sizeof(int16_t));
      Serial.println();
      Serial.println("DATA_END");
    }
   
    if (cmd=="S") {
      digitalWrite(RELAY_PIN, state);
      state ^= 1 ;
      Serial.println(state);
    }
  }
}