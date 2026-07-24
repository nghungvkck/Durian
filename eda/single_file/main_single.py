"""
Chạy Single File Analysis độc lập
"""

import tkinter as tk
from .gui_single import SingleFileGUI
from audio_core import get_audio_files


def launch():
    """Khởi chạy Single File Analysis"""
    root = tk.Tk()
    root.title("Single File Analysis - Audio Peak Analyzer")
    root.geometry("1400x900")
    
    # Tìm file mặc định
    audio_files = get_audio_files()
    default_file = audio_files[0] if audio_files else "Recording 4.wav"
    
    app = SingleFileGUI(root, wav_file=default_file)
    root.mainloop()


if __name__ == "__main__":
    launch()