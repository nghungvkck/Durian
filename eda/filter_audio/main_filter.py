"""
Chạy Filter Audio độc lập
"""

import tkinter as tk
from tkinter import ttk
from .gui_filter import FilterAudioGUI


def launch():
    root = tk.Tk()
    root.title("Filter Audio - Audio Analysis")
    root.geometry("1400x900")
    
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    app = FilterAudioGUI(main_frame)
    root.mainloop()


if __name__ == "__main__":
    launch()