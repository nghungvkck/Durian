import serial
import struct
import wave
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# ==========================
# Cấu hình
# ==========================

PORT = "COM9"
BAUD = 921600
SAMPLE_RATE = 16000

RELAY_TIME = 25     # ms
RECORD_TIME = 500    # ms

# ==========================
ser = serial.Serial(PORT, BAUD, timeout=5)
print("Đã kết nối ESP32")

# Bật chế độ interactive
plt.ion()
fig, ax = plt.subplots(figsize=(12, 4))

while True:
    input("\nNhấn Enter để BẮN...")
    # Gửi lệnh
    cmd = f"ON,{RELAY_TIME},{RECORD_TIME}\n"
    ser.write(cmd.encode())

    print("Đang chờ ESP32...")

    # Chờ DATA_BEGIN
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line == "DATA_BEGIN":
            break

    # Đọc số sample
    sampleCount = struct.unpack("<I", ser.read(4))[0]
    print("Sample:", sampleCount)

    # Đọc dữ liệu âm thanh
    audioBytes = ser.read(sampleCount * 2)
    audio = np.frombuffer(audioBytes, dtype=np.int16)

    # Chờ DATA_END
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line == "DATA_END":
            break

    # Lưu WAV
    filename = datetime.now().strftime("%Y%m%d_%H%M%S.wav")

    with wave.open('Recording 4.wav', "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    print("Đã lưu:", filename)

    # ==========================
    # Hiển thị waveform
    # ==========================

    time = np.arange(sampleCount) / SAMPLE_RATE

    ax.clear()
    ax.plot(time, audio, linewidth=0.8)

    ax.set_title(filename)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")

    ax.set_ylim(-32768, 32767)
    ax.grid(True)

    plt.tight_layout()
    plt.draw()
    plt.pause(0.01)