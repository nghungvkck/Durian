import serial
import wave
import threading
from datetime import datetime

PORT = "COM9"
BAUD = 921600
SAMPLE_RATE = 16000

recording = False


def record_audio():
    global recording

    ser = serial.Serial(PORT, BAUD, timeout=1)
    ser.reset_input_buffer()

    filename = datetime.now().strftime("%Y%m%d_%H%M%S.wav")

    wf = wave.open(filename, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(2)      # 16-bit
    wf.setframerate(SAMPLE_RATE)

    print("Đang ghi... Nhấn Enter để dừng.")

    while recording:
        data = ser.read(2048)
        if data:
            wf.writeframesraw(data)

    # Đọc nốt dữ liệu còn trong buffer
    while ser.in_waiting:
        wf.writeframesraw(ser.read(ser.in_waiting))

    wf.close()
    ser.close()

    print("Đã lưu:", filename)


input("Nhấn Enter để bắt đầu ghi...")

recording = True

t = threading.Thread(target=record_audio)
t.start()

input()      # Enter lần 2 để dừng

recording = False

t.join()