import serial
import wave
import os
import time
import struct
from datetime import datetime

PORT = "COM9"
BAUD = 921600
SAMPLE_RATE = 16000

SAVE_DIR = "../src/dataset"
folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")  
full_path = os.path.join(SAVE_DIR, folder_name)
os.makedirs(full_path, exist_ok=True)

status = input("Nhập status: ").strip()
RELAY_TIME = int(input("Thời gian relay (ms): "))
RECORD_TIME = int(input("Thời gian ghi âm (ms): "))
# NUM_SHOTS = int(input("Số lần đấm: "))
# INTERVAL_TIME = int(input("Thời gian nghỉ giữa các lần đấm (ms): "))

ser = serial.Serial(PORT, BAUD, timeout=5)
time.sleep(2)
ser.reset_input_buffer()

for shot in range(1, 11):
    command = f"{status},{RELAY_TIME},{RECORD_TIME}\n"
    ser.write(command.encode())
    print(f"\nĐã gửi lệnh lần {shot}")

    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line == "SHOT_BEGIN":
            break

    sample_count_data = ser.read(4)
    sample_count = struct.unpack("<I", sample_count_data)[0]
    audio_bytes = sample_count * 2
    audio_data = b""

    while len(audio_data) < audio_bytes:
        data = ser.read(audio_bytes - len(audio_data))
        if not data:
            print("Lỗi: không nhận đủ dữ liệu!")
            break
        audio_data += data

    filename = f"shot_{shot:03d}.wav"
    filepath = os.path.join(full_path, filename)

    with wave.open(filepath, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(audio_data)

    print(f"Đã lưu {filename}")

    if shot < 10:
        # print(f"Nghỉ {11} ms...")
        time.sleep(3)

print("\nĐÃ THU XONG!")
ser.close()