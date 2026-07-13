import serial
import threading
from datetime import datetime

cams = [
    # ("cam1", serial.Serial("COM12", 921600, timeout=10)),
    ("cam2", serial.Serial("COM15", 921600, timeout=10))
]

capture_id = 1

def capture(name, ser, timestamp, idx):

    ser.reset_input_buffer()
    ser.write(b"c\n")

    # Chờ IMG_BEGIN
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line == "IMG_BEGIN":
            break

    size = int(ser.readline().decode().strip())

    jpg = bytearray()

    while len(jpg) < size:
        data = ser.read(min(512, size - len(jpg)))
        if not data:
            print(name, "Timeout!")
            return

        jpg.extend(data)

    ser.readline()      # IMG_END

    filename = f"{timestamp}_{name}_{idx:04d}.jpg"

    with open(filename, "wb") as f:
        f.write(jpg)

    print(f"{name} -> {filename}")

while True:

    cmd = input("Nhập c hoặc q: ").strip()

    if cmd == "q":
        break

    if cmd != "c":
        continue

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    threads = []

    for name, ser in cams:
        t = threading.Thread(
            target=capture,
            args=(name, ser, timestamp, capture_id)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    capture_id += 1

for _, ser in cams:
    ser.close()