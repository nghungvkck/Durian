import serial
import wave
import time
from datetime import datetime

PORT = "COM9"
BAUD = 115200
SAMPLE_RATE = 16000

ser = serial.Serial(PORT, BAUD, timeout=0.1)
time.sleep(2)
ser.reset_input_buffer()

input("Nhấn Enter để bắt đầu ghi...")
record_time = float(input("Nhập thời gian ghi (giây): "))
BYTES_TO_READ = int(SAMPLE_RATE * 2 * record_time)

audio = bytearray()

print("Đang ghi...")

while len(audio) < BYTES_TO_READ:
    remain = BYTES_TO_READ - len(audio)
    data = ser.read(min(512, remain))
    if data:
        audio.extend(data)

filename = datetime.now().strftime("%Y%m%d_%H%M%S.wav")

with wave.open(filename, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio)

ser.close()

print("Đã lưu:", filename)
print("Số byte:", len(audio))