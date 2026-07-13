#include <Arduino.h>
#include <driver/i2s.h>

#define I2S_PORT I2S_NUM_0

#define relay 7

#define I2S_WS   10
#define I2S_SCK  11
#define I2S_SD   9

#define SAMPLE_RATE 16000
#define BUFFER_SIZE 256 

int32_t samples[BUFFER_SIZE];  // tạo 1 mản để luu dữ liệu đọc được từ i2s_read()

void setup()
{
    Serial.begin(115200);

    pinMode(relay, OUTPUT);

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

    i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_PORT, &pin_config);
    i2s_zero_dma_buffer(I2S_PORT);

    Serial.println("ICS43434 Ready");
}

void loop()
{

    if ( Serial.available()){
        String cmd = Serial.readStringUntil('\n'); // đọc String mà người dùng nhập vào serial
        cmd.trim();
        // tach chuoi trong c++
        int p1= cmd.indexOf(',');
        int p2 = cmd.indexOf(',' , p1+1);

        String status = cmd.substring(0,p1);
        String delayStr = cmd.substring(p1+1, p2);
        String recording = cmd.substring(p2+1);

        // chuyển đổi trạng thái
        int time_delay = delayStr.toInt();
        int time_recording = recording.toInt();

        if ( status == "on"){
          digitalWrite(relay, HIGH);
          delay(time_delay);
          digitalWrite(relay, LOW);

        long startTime = millis();
          size_t bytesRead;
          while(millis() - startTime  <  time_recording){
            i2s_read(
                I2S_PORT,
                samples,
                sizeof(samples),
                &bytesRead,
                portMAX_DELAY
            );
            int count = bytesRead / sizeof(int32_t);

            for ( int  i=0; i < count; i++){
              int32_t sample = samples[i];
              int16_t sample16 = samples[i] >> 16;
              Serial.write((uint8_t *)&sample16, sizeof(sample16));
            }
          }
        }
    }
}