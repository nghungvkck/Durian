"""
File chạy Compare Tools
"""

import tkinter as tk
from tkinter import ttk

from .gui_compare import CompareToolsGUI


def launch():
    """Khởi chạy Compare Tools"""
    root = tk.Tk()
    root.title("Compare Tools - Audio Analysis")
    root.geometry("1400x900")
    
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    app = CompareToolsGUI(main_frame)
    root.mainloop()


if __name__ == "__main__":
    launch()