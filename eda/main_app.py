"""
Ứng dụng chính - Kết hợp Single File, Compare Tools và Filter Audio
"""

import tkinter as tk
from tkinter import ttk
import os

from single_file import SingleFileGUI
from compare_tools import CompareToolsGUI
from filter_audio import FilterAudioGUI
from audio_core import get_audio_files


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Analysis - Sầu Riêng Edition")
        self.root.geometry("1450x920")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, 
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Single File
        self.tab_single = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_single, text="📊 Single File")
        self.init_single_file_tab()
        
        # Tab 2: Compare
        self.tab_compare = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_compare, text="📈 Compare")
        self.init_compare_tab()
        
        # Tab 3: Filter Audio
        self.tab_filter = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_filter, text="🎵 Filter Audio")
        self.init_filter_tab()
    
    def init_single_file_tab(self):
        container = ttk.Frame(self.tab_single)
        container.pack(fill=tk.BOTH, expand=True)
        
        audio_files = get_audio_files()
        default_file = audio_files[0] if audio_files else "Recording 4.wav"
        
        self.single_app = SingleFileGUI(container, wav_file=default_file)
        self.single_app.status_bar = self.status_bar
        self.single_app.status_var = self.status_var
    
    def init_compare_tab(self):
        container = ttk.Frame(self.tab_compare)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.compare_app = CompareToolsGUI(container)
        self.compare_app.status_bar = self.status_bar
        self.compare_app.status_var = self.status_var
    
    def init_filter_tab(self):
        container = ttk.Frame(self.tab_filter)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.filter_app = FilterAudioGUI(container)
        self.filter_app.status_bar = self.status_bar
        self.filter_app.status_var = self.status_var


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()