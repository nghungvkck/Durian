import serial
import wave
import numpy as np

PORT = "COM9"
BAUD = 115200
SAMPLE_RATE = 16000

ser = serial.Serial(PORT, BAUD, timeout=0.1)

# Gửi lệnh
ser.write(b"on,500,3\n")

audio = bytearray()

while True:

    data = ser.read(512)

    if data:
        audio.extend(data)

    # ESP32 báo đã xong
    if b"DONE\n" in audio:
        pos = audio.find(b"DONE\n")

        audio = audio[:pos]
        break

ser.close()

audio = np.frombuffer(audio, dtype=np.int16)

with wave.open("record.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio.tobytes())

print("Đã lưu record.wav")