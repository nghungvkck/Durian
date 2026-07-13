import serial
import sys
import time
import os

PORT = "COM3"
BAUD = 115200
OUTPUT_FILE = "capture.jpg"


def read_line(ser):
    return ser.readline().decode(errors="ignore").strip()


def capture(ser):
    ser.reset_input_buffer()
    ser.write(b"c\n")

    # Wait for IMG_BEGIN, ignoring any stray boot/log lines
    for _ in range(50):
        line = read_line(ser)
        if line == "IMG_BEGIN":
            break
        if line == "ERR":
            print("ESP32 báo lỗi chụp ảnh (ERR). Thử lại.")
            return False
    else:
        print("Không nhận được IMG_BEGIN, timeout.")
        return False

    # Next line is the image length
    length_line = read_line(ser)
    try:
        length = int(length_line)
    except ValueError:
        print(f"Không đọc được kích thước ảnh: {length_line!r}")
        return False

    print(f"Đang nhận {length} byte...")
    data = ser.read(length)
    if len(data) != length:
        print(f"Nhận thiếu dữ liệu: {len(data)}/{length} byte")
        return False

    # Consume trailing blank line + IMG_END
    for _ in range(5):
        line = read_line(ser)
        if line == "IMG_END":
            break

    with open(OUTPUT_FILE, "wb") as f:
        f.write(data)

    print(f"Đã lưu ảnh: {os.path.abspath(OUTPUT_FILE)}")
    return True


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else PORT
    print(f"Đang kết nối {port} @ {BAUD} baud...")
    ser = serial.Serial(port, BAUD, timeout=5)
    time.sleep(2)  # đợi board reset xong sau khi mở cổng serial

    ok = capture(ser)
    ser.close()

    if ok:
        os.startfile(OUTPUT_FILE)


if __name__ == "__main__":
    main()
