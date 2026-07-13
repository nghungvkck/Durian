import tkinter as tk
import serial

# =====================
# COM của ESP32
# =====================
esp = serial.Serial("COM9", 115200, timeout=1)


def open_valve():
    esp.write(b"ON\n")


def close_valve():
    esp.write(b"OFF\n")


window = tk.Tk()
window.title("Điều khiển van điện từ")
window.geometry("320x180")


label = tk.Label(
    window,
    text="ESP32 Valve Control",
    font=("Arial", 16)
)
label.pack(pady=15)


btn_on = tk.Button(
    window,
    text="MỞ VAN",
    bg="green",
    fg="white",
    width=18,
    height=2,
    command=open_valve
)
btn_on.pack(pady=8)


btn_off = tk.Button(
    window,
    text="ĐÓNG VAN",
    bg="red",
    fg="white",
    width=18,
    height=2,
    command=close_valve
)
btn_off.pack()


window.mainloop()

esp.close()