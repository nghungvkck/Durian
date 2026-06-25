import serial
import csv

ser = serial.Serial('COM9', 115200)

count = 0
max_rows = 5
with open("dataset.csv", "a", newline="") as f:
    writer = csv.writer(f)
    while count < max_rows:
        line = ser.readline().decode().strip()
        if not line:
            continue

        if line in ["START", "DONE"]:
            continue

        data = line.split(";")

        if len(data) == 5:
            writer.writerow(data)
            f.flush()
            count += 1
            print(f"Saved {count}/{max_rows}: {data}")

print("Đã lưu đủ 5 dòng.")
ser.close()