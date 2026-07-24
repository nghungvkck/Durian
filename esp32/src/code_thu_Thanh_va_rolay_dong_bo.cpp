#include <Arduino.h>
#include <driver/i2s.h>

#define I2S_PORT I2S_NUM_0
#define RELAY_PIN 7

#define I2S_WS 10
#define I2S_SCK 11
#define I2S_SD 9

#define SAMPLE_RATE 16000
#define BUFFER_SIZE 256

#define PUNCH_INTERVAL 1500
#define MAX_RECORD_TIME 30000
#define MAX_SAMPLES ((SAMPLE_RATE * MAX_RECORD_TIME) / 1000)

int32_t samples[BUFFER_SIZE];
int16_t audioBuffer[MAX_SAMPLES];

void setup() {
    Serial.begin(921600);
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);

    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = BUFFER_SIZE,
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

    i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_PORT, &pin_config);
    i2s_zero_dma_buffer(I2S_PORT);

    Serial.println("ICS43434 Ready");
}

void loop() {
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        int p1 = cmd.indexOf(',');
        int p2 = cmd.indexOf(',', p1 + 1);

        if (p1 == -1 || p2 == -1) {
            return;
        }

        String status = cmd.substring(0, p1);
        int relayTime = cmd.substring(p1 + 1, p2).toInt();
        int numPunches = cmd.substring(p2 + 1).toInt();

        status.toLowerCase();

        if (status == "on" && relayTime > 0 && numPunches > 0) {
            recordAndPunch(relayTime, numPunches);
        }
    }
}

void recordAndPunch(int relayTime, int numPunches) {
    uint32_t sampleCount = 0;
    uint32_t punchCount = 0;
    uint32_t lastPunchTime = 0;
    uint32_t relayStartTime = 0;

    bool relayActive = false;
    bool firstPunch = true;

    i2s_zero_dma_buffer(I2S_PORT);

    while (true) {
        uint32_t now = millis();

        if (!relayActive && punchCount < numPunches) {
            if (firstPunch || now - lastPunchTime >= PUNCH_INTERVAL) {
                digitalWrite(RELAY_PIN, HIGH);
                relayActive = true;
                relayStartTime = now;
                punchCount++;
                firstPunch = false;
            }
        }

        if (relayActive && now - relayStartTime >= relayTime) {
            digitalWrite(RELAY_PIN, LOW);
            relayActive = false;
            lastPunchTime = now;
        }

        size_t bytesRead = 0;

        esp_err_t result = i2s_read(
            I2S_PORT,
            samples,
            sizeof(samples),
            &bytesRead,
            10 / portTICK_PERIOD_MS
        );

        if (result == ESP_OK && bytesRead > 0) {
            int count = bytesRead / sizeof(int32_t);

            for (int i = 0; i < count; i++) {
                if (sampleCount < MAX_SAMPLES) {
                    audioBuffer[sampleCount] = samples[i] >> 16;
                    sampleCount++;
                }
            }
        }

        if (punchCount >= numPunches && !relayActive) {
            break;
        }
    }

    digitalWrite(RELAY_PIN, LOW);

    Serial.println("SHOT_BEGIN");
    delay(2);

    Serial.write(
        (uint8_t*)&sampleCount,
        sizeof(sampleCount)
    );

    Serial.write(
        (uint8_t*)audioBuffer,
        sampleCount * sizeof(int16_t)
    );

    Serial.flush();
}