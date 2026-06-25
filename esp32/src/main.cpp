#include <Arduino.h>
#include <driver/i2s.h>
#include <math.h>

// =========================
#define I2S_SCK 7
#define I2S_WS  5
#define I2S_SD  6
#define I2S_PORT I2S_NUM_0

#define SAMPLE_RATE 16000
#define BUFF_LEN 512

#define THRESHOLD 4000
#define RECORD_TIME 5000

bool recording = false;
unsigned long startTime = 0;

// =========================
// FEATURE ACCUMULATOR
// =========================
float sumRMS = 0;
float sumZCR = 0;
float sumEnergy = 0;
float sumPeak = 0;
float sumCentroid = 0;

int frameCount = 0;

// =========================
// FEATURES
// =========================
float calcRMS(int16_t *x, int N){
    float sum = 0;
    for(int i=0;i<N;i++) sum += x[i]*x[i];
    return sqrt(sum/N);
}

float calcZCR(int16_t *x, int N){
    int c=0;
    for(int i=1;i<N;i++){
        if((x[i-1]>0 && x[i]<0)||(x[i-1]<0 && x[i]>0))
            c++;
    }
    return (float)c/(N-1);
}

float calcEnergy(int16_t *x, int N){
    float s=0;
    for(int i=0;i<N;i++) s += x[i]*x[i];
    return s;
}

float calcPeak(int16_t *x, int N){
    int16_t p=0;
    for(int i=0;i<N;i++){
        int16_t v=abs(x[i]);
        if(v>p) p=v;
    }
    return p;
}

// =========================
// SIMPLE SPECTRAL CENTROID ONLY (FAST)
// =========================
float calcCentroidSimple(int16_t *x, int N){
    float sum=0;
    float wsum=0;

    for(int i=0;i<N;i++){
        float mag = abs(x[i]);
        float freq = (i * SAMPLE_RATE)/N;
        sum += mag;
        wsum += mag * freq;
    }

    return (sum==0)?0:wsum/sum;
}

// =========================
void setup(){
    Serial.begin(115200);

    i2s_config_t config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER|I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = 0,
        .dma_buf_count = 8,
        .dma_buf_len = 64,
        .use_apll = false
    };

    i2s_pin_config_t pin = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = -1,
        .data_in_num = I2S_SD
    };

    i2s_driver_install(I2S_PORT, &config, 0, NULL);
    i2s_set_pin(I2S_PORT, &pin);

    Serial.println("READY");
}

void loop(){

    int32_t raw[BUFF_LEN];
    size_t bytes;

    i2s_read(I2S_PORT, raw, sizeof(raw), &bytes, portMAX_DELAY);

    int N = bytes / 4;

    int16_t pcm[BUFF_LEN];
    float energyDetect = 0;

    for(int i=0;i<N;i++){
        pcm[i] = raw[i] >> 16;
        energyDetect += pcm[i]*pcm[i];
    }

    float rmsDetect = sqrt(energyDetect/N);

    // =========================
    // TRIGGER
    // =========================
    if(!recording){
        if(rmsDetect > THRESHOLD){
            recording = true;
            startTime = millis();

            // reset stats
            sumRMS = sumZCR = sumEnergy = sumPeak = sumCentroid = 0;
            frameCount = 0;

            Serial.println("START");
        }
        return;
    }

    // =========================
    // PROCESS FRAME
    // =========================
    float rms = calcRMS(pcm, N);
    float zcr = calcZCR(pcm, N);
    float energy = calcEnergy(pcm, N);
    float peak = calcPeak(pcm, N);
    float centroid = calcCentroidSimple(pcm, N);

    sumRMS += rms;
    sumZCR += zcr;
    sumEnergy += energy;
    sumPeak += peak;
    sumCentroid += centroid;

    frameCount++;

    // =========================
    // END 5s
    // =========================
    if(millis() - startTime >= RECORD_TIME){

        Serial.print(sumRMS/frameCount); Serial.print(";");
        Serial.print(sumZCR/frameCount); Serial.print(";");
        Serial.print(sumEnergy/frameCount); Serial.print(";");
        Serial.print(sumPeak/frameCount); Serial.print(";");
        Serial.println(sumCentroid/frameCount);

        Serial.println("DONE");

        recording = false;
    }
}


