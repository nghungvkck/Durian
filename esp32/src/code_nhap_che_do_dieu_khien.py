import serial
import wave
import time
from datetime import datetime

PORT = "COM9"
BAUD = 921600
SAMPLE_RATE = 16000

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
ser.reset_input_buffer()

mode = input("Nhập chế độ (H/L/on): ").strip()

# =========================
# Bật relay
# =========================
if mode == "H":
    ser.write(b"H\n")
    print("Đã bật relay")

# =========================
# Tắt relay
# =========================
elif mode == "L":
    ser.write(b"L\n")
    print("Đã tắt relay")

# =========================
# Chế độ tự động
# =========================
elif mode == "on":

    time_delay = int(input("Delay (ms): "))
    record_time = int(input("Thời gian ghi (giây): "))
    status = input("Trạng thái (P): ").strip()

    cmd = f"on,{time_delay},{record_time*1000},{status}\n"

    for i in range(10):
        ser.write(cmd.encode())
        expected_bytes = SAMPLE_RATE * 2 * record_time
        audio = bytearray()

        while len(audio) < expected_bytes:
            remain = expected_bytes - len(audio)
            data = ser.read(min(512, remain))
            if data:
                audio.extend(data)

        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f.wav")

        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio)

        print(f"Lần {i+1}: {filename}")  
        time.sleep(2) 
else:
    print("Lệnh không hợp lệ.")

ser.close()