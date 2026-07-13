import serial
import sys
import time
import os
import threading

BAUD = 115200
OUT_DIR = "calib_images"


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
        results[key] = f"[{key}] incomplete: {len(data)}/{length}"
        return

    for _ in range(5):
        line = read_line(ser)
        if line == "IMG_END":
            break

    with open(output_file, "wb") as f:
        f.write(data)

    results[key] = f"[{key}] OK -> {output_file}"


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
        print("Cách dùng: python capture_calib_set.py COM3 COM4 [so_luong_cap]")
        sys.exit(1)

    left_port, right_port = sys.argv[1], sys.argv[2]
    n_pairs = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    os.makedirs(OUT_DIR, exist_ok=True)

    idx = 0
    print("Đặt checkerboard vào khung hình cả 2 camera, thay đổi góc/khoảng cách mỗi lần.")
    while idx < n_pairs:
        input(f"\n[{idx+1}/{n_pairs}] Enter để chụp cặp ảnh tiếp theo (Ctrl+C để dừng sớm)...")

        results = {}
        left_file = os.path.join(OUT_DIR, f"left_{idx:02d}.jpg")
        right_file = os.path.join(OUT_DIR, f"right_{idx:02d}.jpg")

        t1 = threading.Thread(target=capture_from_port, args=(left_port, left_file, results))
        t2 = threading.Thread(target=capture_from_port, args=(right_port, right_file, results))
        t1.start(); t2.start()
        t1.join(); t2.join()

        print(results.get(left_port), "|", results.get(right_port))

        ok = "OK" in results.get(left_port, "")
        ok2 = "OK" in results.get(right_port, "")
        if ok and ok2:
            idx += 1
        else:
            print("Lỗi chụp cặp này, thử lại (không tăng số thứ tự).")


if __name__ == "__main__":
    main()
