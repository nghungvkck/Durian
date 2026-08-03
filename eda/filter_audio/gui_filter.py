"""
Giao diện Filter Audio - Lọc tần số và vẽ lại waveform
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import scipy.io.wavfile as wavfile

from audio_core import get_audio_files, load_audio, format_file_display
from audio_core.audio_analyzer import AudioAnalyzer


class FilterAudioGUI:
    """Giao diện lọc tần số và vẽ lại waveform"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Data
        self.data = None
        self.samplerate = None
        self.time_axis = None
        self.total_time = 0
        self.length = 0
        self.current_file = None
        self.filtered_data = None
        
        # FFT data
        self.fft_data = None
        self.freq_axis = None
        
        # Parameters
        self.min_freq = tk.DoubleVar(value=0)
        self.max_freq = tk.DoubleVar(value=4000)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = None
        
        self.setup_ui()
        self.refresh_file_list()
    
    def setup_ui(self):
        """Thiết lập giao diện Filter Audio"""
        main_panel = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True)
        
        # === PANEL TRÁI ===
        left_frame = ttk.Frame(main_panel, width=380)
        main_panel.add(left_frame, weight=1)
        
        # Scroll
        canvas = tk.Canvas(left_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scroll_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW, width=370)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === NỘI DUNG ===
        ttk.Label(scroll_frame, text="🎵 Filter Audio", font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=5)
        
        # 1. Danh sách file
        file_frame = ttk.LabelFrame(scroll_frame, text="📁 Audio Files", padding=5)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        list_container = ttk.Frame(file_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scroll = ttk.Scrollbar(list_container, orient=tk.VERTICAL)
        self.file_listbox = tk.Listbox(list_container, yscrollcommand=scroll.set,
                                       font=('Consolas', 9), selectmode=tk.SINGLE,
                                       bg='#2b2b2b', fg='#e0e0e0',
                                       selectbackground='#0078d4', height=6)
        scroll.config(command=self.file_listbox.yview)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_file_list).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(btn_frame, text="📂 Browse", command=self.browse_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        # 2. File info
        info_frame = ttk.LabelFrame(scroll_frame, text="📋 Current File", padding=5)
        info_frame.pack(fill=tk.X, pady=5)
        self.file_label = ttk.Label(info_frame, text="No file selected", font=('Arial', 10, 'bold'))
        self.file_label.pack(anchor=tk.W)
        self.file_info_label = ttk.Label(info_frame, text="", font=('Arial', 9))
        self.file_info_label.pack(anchor=tk.W)
        
        # 3. Frequency Filter - Chọn vùng cần GIỮ LẠI
        filter_frame = ttk.LabelFrame(scroll_frame, text="🎯 Keep Frequency Range (Hz)", padding=5)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Chọn khoảng tần số muốn GIỮ LẠI", 
                 font=('Arial', 9, 'italic')).pack(anchor=tk.W, pady=2)
        
        row1 = ttk.Frame(filter_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Min Freq (Hz):", width=14).pack(side=tk.LEFT)
        self.min_entry = ttk.Entry(row1, width=10, textvariable=self.min_freq)
        self.min_entry.pack(side=tk.LEFT, padx=3)
        
        row2 = ttk.Frame(filter_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Max Freq (Hz):", width=14).pack(side=tk.LEFT)
        self.max_entry = ttk.Entry(row2, width=10, textvariable=self.max_freq)
        self.max_entry.pack(side=tk.LEFT, padx=3)
        
        # Nút Apply Filter
        filter_btn_frame = ttk.Frame(filter_frame)
        filter_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(filter_btn_frame, text="🔍 Apply Filter", 
                  command=self.apply_filter).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(filter_btn_frame, text="🔄 Reset", 
                  command=self.reset_filter).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 4. Export
        export_frame = ttk.LabelFrame(scroll_frame, text="💾 Export", padding=5)
        export_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(export_frame, text="📁 Export Filtered WAV", 
                  command=self.export_filtered_wav).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="📊 Export Comparison CSV", 
                  command=self.export_comparison).pack(fill=tk.X, pady=2)
        
        # 5. Info
        info_frame = ttk.LabelFrame(scroll_frame, text="📊 Info", padding=5)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.info_text = tk.Text(info_frame, height=4, font=('Consolas', 9),
                                bg='#1e1e1e', fg='#d4d4d4')
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # === PANEL PHẢI ===
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=3)
        
        self.fig = Figure(figsize=(10, 10), dpi=100)
        
        # Subplot 1: Waveform gốc
        self.ax1 = self.fig.add_subplot(411)
        self.ax1.set_title('Original Waveform', fontsize=10)
        self.ax1.set_xlabel('Time (s)', fontsize=9)
        self.ax1.set_ylabel('Amplitude', fontsize=9)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.tick_params(labelsize=8)
        self.line_orig, = self.ax1.plot([], [], 'b-', linewidth=0.8)
        
        # Subplot 2: Waveform đã filter
        self.ax2 = self.fig.add_subplot(412)
        self.ax2.set_title('Filtered Waveform (click "Apply Filter")', fontsize=10)
        self.ax2.set_xlabel('Time (s)', fontsize=9)
        self.ax2.set_ylabel('Amplitude', fontsize=9)
        self.ax2.grid(True, alpha=0.3)
        self.ax2.tick_params(labelsize=8)
        self.line_filtered, = self.ax2.plot([], [], 'r-', linewidth=0.8)
        
        # Subplot 3: FFT gốc với vùng chọn
        self.ax3 = self.fig.add_subplot(413)
        self.ax3.set_title('FFT - Select region to keep', fontsize=10)
        self.ax3.set_xlabel('Frequency (Hz)', fontsize=9)
        self.ax3.set_ylabel('Magnitude', fontsize=9)
        self.ax3.grid(True, alpha=0.3)
        self.ax3.tick_params(labelsize=8)
        self.line_fft_orig, = self.ax3.plot([], [], 'b-', linewidth=1)
        
        # Subplot 4: FFT đã filter
        self.ax4 = self.fig.add_subplot(414)
        self.ax4.set_title('Filtered FFT', fontsize=10)
        self.ax4.set_xlabel('Frequency (Hz)', fontsize=9)
        self.ax4.set_ylabel('Magnitude', fontsize=9)
        self.ax4.grid(True, alpha=0.3)
        self.ax4.tick_params(labelsize=8)
        self.line_fft_filtered, = self.ax4.plot([], [], 'r-', linewidth=1)
        
        self.fig.subplots_adjust(
            left=0.08, right=0.95, bottom=0.05, top=0.95,
            hspace=0.45, wspace=0.2
        )
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(self.canvas, right_frame)
        toolbar.update()
    
    def refresh_file_list(self):
        """Làm mới danh sách file"""
        self.file_listbox.delete(0, tk.END)
        audio_files = get_audio_files(self.current_dir)
        if not audio_files:
            self.file_listbox.insert(tk.END, "⚠️ No audio files")
            return
        for i, f in enumerate(audio_files):
            self.file_listbox.insert(tk.END, format_file_display(f, i))
        self.update_status(f"Found {len(audio_files)} files")
    
    def browse_file(self):
        """Browse chọn file"""
        filepath = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio files", "*.wav *.WAV *.mp3 *.MP3 *.m4a *.M4A *.flac *.FLAC *.ogg *.OGG")]
        )
        if filepath:
            self.load_file(filepath)
            self.refresh_file_list()
    
    def on_file_select(self, event):
        """Click chọn file"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        audio_files = get_audio_files(self.current_dir)
        if index < len(audio_files):
            self.load_file(audio_files[index])
    
    def load_file(self, filepath):
        """Load file audio"""
        self.update_status(f"Loading: {os.path.basename(filepath)}...")
        data, sr, _ = load_audio(filepath)
        
        if data is None:
            self.update_status(f"❌ Failed to load: {os.path.basename(filepath)}")
            return
        
        self.data = data
        self.samplerate = sr
        self.length = len(data)
        self.time_axis = np.linspace(0, self.length/sr, self.length)
        self.total_time = self.length/sr
        self.current_file = filepath
        self.filtered_data = None
        
        self.file_label.config(text=os.path.basename(filepath))
        self.file_info_label.config(text=f"Rate: {sr} Hz | Duration: {self.total_time:.2f}s")
        
        # Vẽ waveform gốc
        self.line_orig.set_data(self.time_axis, data)
        self.ax1.set_xlim(0, self.total_time)
        y_max = max(np.max(np.abs(data)), 0.1)
        self.ax1.set_ylim(-y_max*1.1, y_max*1.1)
        
        # Vẽ FFT gốc
        fft_data = np.abs(np.fft.fft(data))[:len(data)//2]
        freq_axis = np.fft.fftfreq(len(data), d=1/sr)[:len(data)//2]
        if np.max(fft_data) > 0:
            fft_data = fft_data / np.max(fft_data)
        
        self.fft_data = fft_data
        self.freq_axis = freq_axis
        
        self.line_fft_orig.set_data(freq_axis[:4000], fft_data[:4000])
        self.ax3.set_xlim(0, 4000)
        self.ax3.set_ylim(0, 1.1)
        self.ax3.set_title('FFT - Select region to keep', fontsize=10)
        
        # Clear filtered plots
        self.line_filtered.set_data([], [])
        self.line_fft_filtered.set_data([], [])
        self.ax2.set_ylim(-y_max*1.1, y_max*1.1)
        self.ax2.set_xlim(0, self.total_time)
        self.ax2.set_title('Filtered Waveform (click "Apply Filter")', fontsize=10)
        self.ax4.set_xlim(0, 4000)
        self.ax4.set_ylim(0, 1.1)
        self.ax4.set_title('Filtered FFT', fontsize=10)
        
        self.canvas.draw()
        self.update_status(f"Loaded: {os.path.basename(filepath)}")
        
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', f"📂 {os.path.basename(filepath)}\n")
        self.info_text.insert(tk.END, f"   Rate: {sr} Hz\n")
        self.info_text.insert(tk.END, f"   Duration: {self.total_time:.2f}s\n")
        self.info_text.insert(tk.END, f"   Samples: {self.length:,}\n")
        self.info_text.insert(tk.END, f"\n🎯 Set Min/Max Freq and click Apply Filter")
    
    def apply_filter(self):
        """Áp dụng filter và vẽ lại waveform"""
        if self.data is None:
            messagebox.showwarning("Warning", "Please load a file first!")
            return
        
        try:
            min_freq = self.min_freq.get()
        except:
            min_freq = 0
            self.min_freq.set(0)
        
        try:
            max_freq = self.max_freq.get()
        except:
            max_freq = 4000
            self.max_freq.set(4000)
        
        if min_freq >= max_freq:
            messagebox.showwarning("Warning", "Min Freq must be less than Max Freq!")
            return
        
        self.update_status(f"Filtering: keeping {min_freq:.0f}-{max_freq:.0f}Hz...")
        
        # Áp dụng lọc
        self.filtered_data = AudioAnalyzer.apply_filter_and_inverse_fft(
            self.data, self.samplerate, min_freq, max_freq
        )
        
        # Vẽ waveform đã filter
        self.line_filtered.set_data(self.time_axis, self.filtered_data)
        self.ax2.set_xlim(0, self.total_time)
        y_max = max(np.max(np.abs(self.filtered_data)), 0.1)
        self.ax2.set_ylim(-y_max*1.1, y_max*1.1)
        self.ax2.set_title(f'Filtered Waveform (kept {min_freq:.0f}-{max_freq:.0f}Hz)', fontsize=10)
        
        # Vẽ FFT đã filter
        fft_filtered = np.abs(np.fft.fft(self.filtered_data))[:len(self.filtered_data)//2]
        freq_axis = np.fft.fftfreq(len(self.filtered_data), d=1/self.samplerate)[:len(self.filtered_data)//2]
        if np.max(fft_filtered) > 0:
            fft_filtered = fft_filtered / np.max(fft_filtered)
        self.line_fft_filtered.set_data(freq_axis[:4000], fft_filtered[:4000])
        self.ax4.set_xlim(0, 4000)
        self.ax4.set_ylim(0, 1.1)
        self.ax4.set_title(f'Filtered FFT (kept {min_freq:.0f}-{max_freq:.0f}Hz)', fontsize=10)
        
        # Vẽ vùng giữ lại trên FFT gốc
        self.ax3.clear()
        self.ax3.plot(self.freq_axis[:4000], self.fft_data[:4000], 'b-', linewidth=1, alpha=0.5)
        
        # Vùng GIỮ LẠI (màu xanh)
        self.ax3.axvspan(min_freq, max_freq, alpha=0.3, color='green', label=f'Kept: {min_freq:.0f}-{max_freq:.0f}Hz')
        
        # Vùng BỎ ĐI (màu đỏ)
        if min_freq > 0:
            self.ax3.axvspan(0, min_freq, alpha=0.2, color='red', label='Removed')
        if max_freq < 4000:
            self.ax3.axvspan(max_freq, 4000, alpha=0.2, color='red')
        
        self.ax3.set_title('FFT (green=kept, red=removed)', fontsize=10)
        self.ax3.set_xlabel('Frequency (Hz)', fontsize=9)
        self.ax3.set_ylabel('Magnitude', fontsize=9)
        self.ax3.legend(fontsize=7, loc='upper right')
        self.ax3.grid(True, alpha=0.3)
        self.ax3.set_xlim(0, 4000)
        self.ax3.set_ylim(0, 1.1)
        
        self.canvas.draw()
        
        # Update info
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', f"📂 {os.path.basename(self.current_file)}\n")
        self.info_text.insert(tk.END, f"   Rate: {self.samplerate} Hz\n")
        self.info_text.insert(tk.END, f"   Duration: {self.total_time:.2f}s\n")
        self.info_text.insert(tk.END, f"   Samples: {self.length:,}\n")
        self.info_text.insert(tk.END, f"\n🎯 Kept: {min_freq:.0f} - {max_freq:.0f} Hz\n")
        kept_points = np.sum((self.freq_axis >= min_freq) & (self.freq_axis <= max_freq))
        total_points = len(self.freq_axis)
        self.info_text.insert(tk.END, f"   Kept points: {kept_points} ({kept_points/total_points*100:.1f}%)\n")
        self.info_text.insert(tk.END, f"   Removed points: {total_points - kept_points} ({(total_points-kept_points)/total_points*100:.1f}%)")
        
        self.update_status(f"✅ Filtered: kept {min_freq:.0f}-{max_freq:.0f}Hz")
    
    def reset_filter(self):
        """Reset về trạng thái ban đầu"""
        self.min_freq.set(0)
        self.max_freq.set(4000)
        self.filtered_data = None
        
        if self.data is not None:
            # Vẽ lại waveform gốc
            y_max = max(np.max(np.abs(self.data)), 0.1)
            self.ax2.set_ylim(-y_max*1.1, y_max*1.1)
            self.ax2.set_xlim(0, self.total_time)
            self.ax2.set_title('Filtered Waveform (reset)', fontsize=10)
            self.line_filtered.set_data([], [])
            
            # Reset FFT
            self.ax4.clear()
            self.ax4.set_title('Filtered FFT (reset)', fontsize=10)
            self.ax4.set_xlabel('Frequency (Hz)', fontsize=9)
            self.ax4.set_ylabel('Magnitude', fontsize=9)
            self.ax4.grid(True, alpha=0.3)
            self.ax4.set_xlim(0, 4000)
            self.ax4.set_ylim(0, 1.1)
            self.line_fft_filtered.set_data([], [])
            
            # Reset FFT gốc
            self.ax3.clear()
            self.ax3.plot(self.freq_axis[:4000], self.fft_data[:4000], 'b-', linewidth=1, alpha=0.5)
            self.ax3.set_title('FFT - Select region to keep', fontsize=10)
            self.ax3.set_xlabel('Frequency (Hz)', fontsize=9)
            self.ax3.set_ylabel('Magnitude', fontsize=9)
            self.ax3.grid(True, alpha=0.3)
            self.ax3.set_xlim(0, 4000)
            self.ax3.set_ylim(0, 1.1)
            
            self.canvas.draw()
            
            self.info_text.delete('1.0', tk.END)
            self.info_text.insert('1.0', f"📂 {os.path.basename(self.current_file)}\n")
            self.info_text.insert(tk.END, f"   Rate: {self.samplerate} Hz\n")
            self.info_text.insert(tk.END, f"   Duration: {self.total_time:.2f}s\n")
            self.info_text.insert(tk.END, f"   Samples: {self.length:,}\n")
            self.info_text.insert(tk.END, f"\n🔄 Reset to original")
            
            self.update_status("Reset to original")
    
    def export_filtered_wav(self):
        """Xuất file WAV đã lọc"""
        if self.filtered_data is None:
            messagebox.showwarning("Warning", "Please apply filter first!")
            return
        
        # Tạo thư mục output nếu chưa có
        output_dir = os.path.join(os.getcwd(), "processing_Data")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            min_freq = self.min_freq.get()
            max_freq = self.max_freq.get()
        except:
            min_freq = 0
            max_freq = 4000
        
        default_name = f"{os.path.splitext(os.path.basename(self.current_file))[0]}_filtered_{min_freq:.0f}_{max_freq:.0f}Hz.wav"
        default_path = os.path.join(output_dir, default_name)
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")],
            initialfile=default_name,
            initialdir=output_dir,
            title="Save filtered audio to WAV"
        )
        if not file_path:
            return
        
        self.update_status(f"Exporting filtered audio...")
        
        # Chuẩn hóa về int16
        filtered_int16 = (self.filtered_data * 32767).astype(np.int16)
        wavfile.write(file_path, self.samplerate, filtered_int16)
        
        self.update_status(f"✅ Exported to {os.path.basename(file_path)}")
        messagebox.showinfo(
            "✅ Success", 
            f"Filtered audio saved to:\n{file_path}\n\n"
            f"Frequency range: {min_freq:.0f} - {max_freq:.0f} Hz"
        )
    
    def export_comparison(self):
        """Export CSV so sánh gốc và filter"""
        if self.data is None:
            messagebox.showwarning("Warning", "Please load a file first!")
            return
        
        if self.filtered_data is None:
            messagebox.showwarning("Warning", "Please apply filter first!")
            return
        
        # Tạo thư mục output nếu chưa có
        output_dir = os.path.join(os.getcwd(), "processing_Data")
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"{os.path.splitext(os.path.basename(self.current_file))[0]}_filter_comparison.csv",
            initialdir=output_dir,
            title="Save comparison CSV"
        )
        if not file_path:
            return
        
        # Tính FFT
        fft_orig = np.abs(np.fft.fft(self.data))[:len(self.data)//2]
        fft_filtered = np.abs(np.fft.fft(self.filtered_data))[:len(self.filtered_data)//2]
        freq_axis = np.fft.fftfreq(len(self.data), d=1/self.samplerate)[:len(self.data)//2]
        
        min_len = min(len(fft_orig), len(fft_filtered), len(freq_axis))
        
        np.savetxt(file_path, 
                  np.column_stack((freq_axis[:min_len], fft_orig[:min_len], fft_filtered[:min_len])),
                  delimiter=',', 
                  header='Frequency,Original_Magnitude,Filtered_Magnitude',
                  comments='')
        
        self.update_status(f"✅ Exported comparison to {os.path.basename(file_path)}")
        messagebox.showinfo("Success", f"Exported to:\n{file_path}")
    
    def update_status(self, text):
        self.status_var.set(text)
        if self.status_bar:
            self.status_bar.config(text=text)