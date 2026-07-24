import serial
import sys
import time
import os
import threading

BAUD = 921600


def read_line(ser):
    return ser.readline().decode(errors="ignore").strip()


def capture(ser, output_file, results, key):
    ser.reset_input_buffer()
    ser.write(b"c\n")

    for _ in range(50):
        line = read_line(ser)
        if line == "IMG_BEGIN":
            break
        if line == "ERR":
            results[key] = f"[{key}] ESP32 báo lỗi chụp ảnh (ERR)."
            return
    else:
        results[key] = f"[{key}] Không nhận được IMG_BEGIN, timeout."
        return

    length_line = read_line(ser)
    try:
        length = int(length_line)
    except ValueError:
        results[key] = f"[{key}] Không đọc được kích thước ảnh: {length_line!r}"
        return

    data = ser.read(length)
    if len(data) != length:
        results[key] = f"[{key}] Nhận thiếu dữ liệu: {len(data)}/{length} byte"
        return

    for _ in range(5):
        line = read_line(ser)
        if line == "IMG_END":
            break

    with open(output_file, "wb") as f:
        f.write(data)

    results[key] = f"[{key}] Đã lưu ảnh: {os.path.abspath(output_file)}"


def capture_from_port(port, output_file, results):
    key = port
    try:
        ser = serial.Serial(port, BAUD, timeout=5)
    except serial.SerialException as e:
        results[key] = f"[{key}] Không mở được cổng: {e}"
        return

    time.sleep(2)  # đợi board reset xong sau khi mở cổng serial
    capture(ser, output_file, results, key)
    ser.close()


def main():
    if len(sys.argv) < 3:
        print("Cách dùng: python capture_multi.py COM3 COM5 [COM7 ...]")
        sys.exit(1)

    ports = sys.argv[1:]
    results = {}
    threads = []

    for i, port in enumerate(ports):
        output_file = f"capture_{port}.jpg"
        t = threading.Thread(target=capture_from_port, args=(port, output_file, results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print()
    for port in ports:
        print(results.get(port, f"[{port}] Không có kết quả."))

    for port in ports:
        f = f"capture_{port}.jpg"
        if os.path.exists(f) and results.get(port, "").startswith(f"[{port}] Đã lưu"):
            os.startfile(f)


if __name__ == "__main__":
    main()
