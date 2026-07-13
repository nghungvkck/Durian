import serial
import sys
import time
import os
import threading

BAUD = 115200


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
            results[key] = f"[{key}] ERR"
            return
    else:
        results[key] = f"[{key}] timeout"
        return

    length_line = read_line(ser)
    try:
        length = int(length_line)
    except ValueError:
        results[key] = f"[{key}] bad length: {length_line!r}"
        return

    data = ser.read(length)
    if len(data) != length:
        results[key] = f"[{key}] incomplete"
        return

    for _ in range(5):
        line = read_line(ser)
        if line == "IMG_END":
            break

    with open(output_file, "wb") as f:
        f.write(data)

    results[key] = f"[{key}] OK"


def capture_from_port(port, output_file, results):
    key = port
    try:
        ser = serial.Serial(port, BAUD, timeout=5)
    except serial.SerialException as e:
        results[key] = f"[{key}] open failed: {e}"
        return
    time.sleep(2)
    capture(ser, output_file, results, key)
    ser.close()


def main():
    if len(sys.argv) < 3:
        print("Cách dùng: python test_frame.py COM3 COM4")
        sys.exit(1)

    left_port, right_port = sys.argv[1], sys.argv[2]
    left_file, right_file = "test_left.jpg", "test_right.jpg"

    while True:
        input("\nĐặt checkerboard vào vị trí muốn kiểm tra, Enter để chụp thử (Ctrl+C để thoát)...")

        results = {}
        t1 = threading.Thread(target=capture_from_port, args=(left_port, left_file, results))
        t2 = threading.Thread(target=capture_from_port, args=(right_port, right_file, results))
        t1.start(); t2.start()
        t1.join(); t2.join()

        print(results.get(left_port), "|", results.get(right_port))

        if "OK" in results.get(left_port, "") and "OK" in results.get(right_port, ""):
            os.startfile(left_file)
            os.startfile(right_file)
            print("Đã mở 2 ảnh test — kiểm tra checkerboard có nằm trọn trong cả 2 khung không.")
        else:
            print("Lỗi chụp, kiểm tra lại kết nối.")


if __name__ == "__main__":
    main()
