import serial
import wave
import os
import time
import struct
from datetime import datetime

PORT = "COM9"
BAUD = 921600
SAMPLE_RATE = 16000
NUM_PUNCHES = 5
SAVE_DIR = "../src/dataset"

def capture_audio(status, relay_time):
    ser = serial.Serial(PORT, BAUD, timeout=5)
    time.sleep(2)
    ser.reset_input_buffer()
    
    command = f"{status},{relay_time},{NUM_PUNCHES}\n"
    ser.write(command.encode())
    print(f"Đã gửi lệnh: {command.strip()}")
    print(f"Đang thực hiện {NUM_PUNCHES} lần đấm...")
    
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line == "SHOT_BEGIN":
            break
    
    print("Đã đấm xong, đang nhận audio...")
    
    sample_count_data = ser.read(4)
    if len(sample_count_data) != 4:
        print("Lỗi: Không nhận đủ sample count!")
        ser.close()
        return None
    
    sample_count = struct.unpack("<I", sample_count_data)[0]
    audio_bytes = sample_count * 2
    audio_data = b""
    
    while len(audio_data) < audio_bytes:
        data = ser.read(audio_bytes - len(audio_data))
        if not data:
            print("Lỗi: Không nhận đủ dữ liệu audio!")
            break
        audio_data += data
    
    filename = datetime.now().strftime("%Y%m%d_%H%M%S.wav")
    filepath = os.path.join(SAVE_DIR, filename)
    
    with wave.open(filepath, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(audio_data)
    
    print(f"Đã lưu file: {filepath}")
    print(f"Số sample: {sample_count}")
    print("ĐÃ THU XONG!")
    
    ser.close()
    return filepath

def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    print("="*50)
    print("CHƯƠNG TRÌNH THU ÂM - NHẤN CTRL+C ĐỂ DỪNG")
    print("="*50)
    
    try:
        # Nhập thông tin lần đầu
        status = input("Nhập status: ").strip().lower()
        relay_time = int(input("Thời gian relay (ms): "))
        
        while True:
            capture_audio(status, relay_time)
            print("\n" + "-"*50)
            print("NHẤN ENTER ĐỂ TIẾP TỤC (dùng tham số cũ), HOẶC CTRL+C ĐỂ THOÁT")
            print("-"*50)
            input()
            
    except KeyboardInterrupt:
        print("\nĐã dừng chương trình!")
    except Exception as e:
        print(f"Lỗi: {e}")
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()