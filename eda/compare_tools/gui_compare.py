"""
Giao diện Compare Tools - Rút gọn, đầy đủ chức năng
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import threading

from audio_core import (
    load_audio, AudioAnalyzer, get_audio_files, 
    format_file_display, save_segments_to_wav, 
    get_segments_range, FeatureManager
)


class CompareToolsGUI:
    """Giao diện Compare Tools - Rút gọn"""
    
    def __init__(self, parent):
        self.parent = parent
        
        # Parameters
        self.threshold = tk.DoubleVar(value=0.1)
        self.pre_peak = tk.DoubleVar(value=0.05)
        self.segment_duration = tk.DoubleVar(value=0.1)
        self.min_distance = tk.DoubleVar(value=0.1)
        self.max_freq = tk.DoubleVar(value=4000)
        
        # Segment selection
        self.segment_start = tk.IntVar(value=0)
        self.segment_end = tk.IntVar(value=0)
        self.total_segments = 0
        
        # Data
        self.all_files = []
        self.selected_file_paths = []
        self.file_data = {}
        self.current_viewing_file = None
        self.file_params = {}
        
        # Colors
        self.colors = ['red', 'blue', 'green', 'purple', 'orange']
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = None
        
        # Auto-compare
        self.auto_compare_enabled = True
        self._update_timer = None
        self._is_updating = False
        
        self.setup_ui()
        self.scan_files()
    
    def setup_ui(self):
        """Thiết lập giao diện rút gọn"""
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
        ttk.Label(scroll_frame, text="📈 Compare Tools", font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=5)
        
        # 1. Danh sách file
        file_frame = ttk.LabelFrame(scroll_frame, text="📁 Audio Files", padding=5)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        list_container = ttk.Frame(file_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scroll = ttk.Scrollbar(list_container, orient=tk.VERTICAL)
        self.file_listbox = tk.Listbox(list_container, yscrollcommand=scroll.set,
                                       font=('Consolas', 9), selectmode=tk.EXTENDED,
                                       bg='#2b2b2b', fg='#e0e0e0',
                                       selectbackground='#0078d4', height=5)
        scroll.config(command=self.file_listbox.yview)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.scan_files).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(btn_frame, text="📂 Browse", command=self.browse_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(btn_frame, text="➕ Add", command=self.add_to_compare).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
        # 2. Files to Compare
        selected_frame = ttk.LabelFrame(scroll_frame, text="📋 Files to Compare", padding=5)
        selected_frame.pack(fill=tk.X, pady=5)
        
        selected_container = ttk.Frame(selected_frame)
        selected_container.pack(fill=tk.X, pady=2)
        
        self.selected_listbox = tk.Listbox(selected_container, height=3,
                                          font=('Consolas', 10),
                                          bg='#1e1e1e', fg='#d4d4d4',
                                          selectbackground='#0078d4')
        self.selected_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.selected_listbox.bind('<<ListboxSelect>>', self.on_selected_click)
        
        ttk.Button(selected_container, text="✖ Remove", command=self.remove_selected_file).pack(side=tk.RIGHT, padx=3)
        
        # 3. Parameters
        param_frame = ttk.LabelFrame(scroll_frame, text="⚙️ Parameters", padding=5)
        param_frame.pack(fill=tk.X, pady=5)
        
        params = [
            ("Threshold:", self.threshold, 0.001, 1.0),
            ("Pre-peak (s):", self.pre_peak, 0, 0.5),
            ("Duration (s):", self.segment_duration, 0.01, 0.5),
            ("Min Distance:", self.min_distance, 0.01, 0.5),
            ("Max Freq (Hz):", self.max_freq, 500, 20000),
        ]
        
        self.param_labels = {}
        for label_text, var, from_val, to_val in params:
            row = ttk.Frame(param_frame)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label_text, width=12).pack(side=tk.LEFT)
            scale = tk.Scale(row, from_=from_val, to=to_val, variable=var,
                           orient=tk.HORIZONTAL, command=self.on_param_change,
                           length=130, resolution=0.001 if var.get() < 1 else 100)
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
            lbl = ttk.Label(row, text=f"{var.get():.2f}" if var.get() < 1 else f"{var.get():.0f}", width=6)
            lbl.pack(side=tk.LEFT, padx=2)
            self.param_labels[label_text] = lbl
        
        self.current_file_label = ttk.Label(param_frame, text="Adjusting: None", font=('Arial', 9, 'italic'))
        self.current_file_label.pack(anchor=tk.W, pady=2)
        
        # 4. Select Segments
        select_frame = ttk.LabelFrame(scroll_frame, text="🎯 Select Segments", padding=5)
        select_frame.pack(fill=tk.X, pady=5)
        
        range_frame = ttk.Frame(select_frame)
        range_frame.pack(fill=tk.X, pady=2)
        ttk.Label(range_frame, text="From:").pack(side=tk.LEFT)
        self.start_spinbox = ttk.Spinbox(range_frame, from_=0, to=100, textvariable=self.segment_start,
                   width=4, command=self.on_segment_range_change)
        self.start_spinbox.pack(side=tk.LEFT, padx=2)
        ttk.Label(range_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.end_spinbox = ttk.Spinbox(range_frame, from_=0, to=100, textvariable=self.segment_end,
                   width=4, command=self.on_segment_range_change)
        self.end_spinbox.pack(side=tk.LEFT, padx=2)
        ttk.Label(range_frame, text="(0=first, -1=last)").pack(side=tk.LEFT, padx=5)
        
        btn_row = ttk.Frame(select_frame)
        btn_row.pack(fill=tk.X, pady=2)
        ttk.Button(btn_row, text="All", command=self.select_all_segments).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(btn_row, text="First 5", command=lambda: self.select_range(0, 4)).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(btn_row, text="Last 5", command=self.select_last_5).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.segments_info_label = ttk.Label(select_frame, text="Total: 0 | Selected: 0", font=('Arial', 9))
        self.segments_info_label.pack(anchor=tk.W, pady=2)
        
        # 5. Actions
        action_frame = ttk.LabelFrame(scroll_frame, text="🔬 Actions", padding=5)
        action_frame.pack(fill=tk.X, pady=5)
        
        btn_row = ttk.Frame(action_frame)
        btn_row.pack(fill=tk.X, pady=2)
        self.auto_btn = ttk.Button(btn_row, text="▶ Auto: ON", command=self.toggle_auto, width=10)
        self.auto_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(btn_row, text="✕ Clear", command=self.clear_compare, width=10).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # 6. Export
        export_frame = ttk.LabelFrame(scroll_frame, text="💾 Export", padding=5)
        export_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(export_frame, text="📁 Export WAV", 
                  command=self.export_all_segments).pack(fill=tk.X, pady=1)
        ttk.Button(export_frame, text="💾 Export CSV", 
                  command=self.export_results).pack(fill=tk.X, pady=1)
        
        # 7. Info
        info_frame = ttk.LabelFrame(scroll_frame, text="📊 Info", padding=5)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.info_text = tk.Text(info_frame, height=4, font=('Consolas', 9),
                                bg='#1e1e1e', fg='#d4d4d4')
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # === PANEL PHẢI ===
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=3)
        
        # Figure lớn hơn để các subplot có không gian
        self.fig = Figure(figsize=(10, 10), dpi=100)
        
        # Subplot 1: Waveform
        self.ax1 = self.fig.add_subplot(311)
        self.ax1.set_title('Waveform - Click file to view', fontsize=10)
        self.ax1.set_xlabel('Time (s)', fontsize=9)
        self.ax1.set_ylabel('Amplitude', fontsize=9)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.tick_params(labelsize=8)
        self.line_wave, = self.ax1.plot([], [], 'b-', linewidth=0.8)
        self.peak_scatter = self.ax1.scatter([], [], color='red', s=20)
        self.segment_patches = []
        
        # Subplot 2: Individual FFTs
        self.ax2 = self.fig.add_subplot(312)
        self.ax2.set_title('Individual FFTs', fontsize=10)
        self.ax2.set_xlabel('Frequency (Hz)', fontsize=9)
        self.ax2.set_ylabel('Magnitude', fontsize=9)
        self.ax2.grid(True, alpha=0.3)
        self.ax2.tick_params(labelsize=8)
        self.fft_lines = []
        
        # Subplot 3: So sánh
        self.ax3 = self.fig.add_subplot(313)
        self.ax3.set_title('Average FFT Comparison', fontsize=10)
        self.ax3.set_xlabel('Frequency (Hz)', fontsize=9)
        self.ax3.set_ylabel('Magnitude', fontsize=9)
        self.ax3.grid(True, alpha=0.3)
        self.ax3.tick_params(labelsize=8)
        self.compare_lines = []
        self.compare_peaks = []
        
        # Điều chỉnh khoảng cách giữa các subplot
        self.fig.subplots_adjust(
            left=0.10,    # Lề trái
            right=0.95,   # Lề phải
            bottom=0.08,  # Lề dưới
            top=0.95,     # Lề trên
            hspace=0.45,  # Khoảng cách dọc GIỮA các subplot
            wspace=0.2    # Khoảng cách ngang
        )
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(self.canvas, right_frame)
        toolbar.update()
    
    # === CÁC HÀM XỬ LÝ ===
    
    def scan_files(self):
        """Quét file audio trong thư mục"""
        self.file_listbox.delete(0, tk.END)
        self.all_files = get_audio_files()
        
        if not self.all_files:
            self.file_listbox.insert(tk.END, "⚠️ No audio files")
            self.status_var.set("No audio files found")
            return
        
        for i, f in enumerate(self.all_files):
            self.file_listbox.insert(tk.END, format_file_display(f, i))
        self.status_var.set(f"Found {len(self.all_files)} files")
        
        # Tự động chọn và load file đầu tiên
        if self.all_files:
            self.file_listbox.selection_set(0)
            self.file_listbox.see(0)
            self.view_file(self.all_files[0])
    
    def browse_file(self):
        """Browse thêm file và tự động thêm vào so sánh"""
        paths = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[("Audio files", "*.wav *.WAV *.mp3 *.MP3 *.m4a *.M4A *.flac *.FLAC *.ogg *.OGG")]
        )
        
        if not paths:
            return
        
        added_count = 0
        first_file = None
        
        for path in paths:
            if path not in self.all_files:
                self.all_files.append(path)
            
            name = os.path.basename(path)
            current = self.selected_listbox.get(0, tk.END)
            
            if name not in current:
                if len(self.selected_file_paths) < 5:
                    self.selected_listbox.insert(tk.END, name)
                    self.selected_file_paths.append(path)
                    added_count += 1
                    if first_file is None:
                        first_file = path
                    self.status_var.set(f"✅ Added: {name}")
                else:
                    self.status_var.set(f"⚠️ Max 5 files! Can't add {name}")
                    break
        
        # Refresh danh sách
        self.scan_files()
        
        # Load file đầu tiên
        if first_file:
            self.view_file(first_file)
            for i, f in enumerate(self.all_files):
                if f == first_file:
                    self.file_listbox.selection_set(i)
                    self.file_listbox.see(i)
                    break
        
        self.status_var.set(f"✅ Added {added_count} file(s)")
        
        # Tự động so sánh nếu có >= 2 file
        if self.auto_compare_enabled and len(self.selected_file_paths) >= 2:
            self.run_compare()
    
    def on_file_select(self, event):
        """Click chọn file"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self.all_files):
            self.view_file(self.all_files[idx])
    
    def view_file(self, filepath):
        """Hiển thị waveform và load tham số riêng"""
        self.status_var.set(f"Loading: {os.path.basename(filepath)}...")
        data, sr, _ = load_audio(filepath)
        
        if data is None:
            self.status_var.set(f"❌ Failed: {os.path.basename(filepath)}")
            self.line_wave.set_data([], [])
            self.ax1.set_title(f'Waveform: {os.path.basename(filepath)} (FAILED)')
            self.ax1.set_xlim(0, 1)
            self.ax1.set_ylim(-0.1, 0.1)
            self.canvas.draw()
            return
        
        self.current_viewing_file = filepath
        
        # Load params
        if filepath in self.file_params:
            p = self.file_params[filepath]
            self.threshold.set(p.get('threshold', 0.1))
            self.pre_peak.set(p.get('pre_peak', 0.05))
            self.segment_duration.set(p.get('duration', 0.1))
            self.min_distance.set(p.get('min_distance', 0.1))
            self.max_freq.set(p.get('max_freq', 4000))
            self.segment_start.set(p.get('seg_start', 0))
            self.segment_end.set(p.get('seg_end', 0))
            self.current_file_label.config(text=f"Adjusting: {os.path.basename(filepath)}")
        else:
            self.current_file_label.config(text=f"Adjusting: {os.path.basename(filepath)} (default)")
        
        threshold = self.threshold.get()
        pre_peak = self.pre_peak.get()
        duration = self.segment_duration.get()
        min_distance = self.min_distance.get()
        max_freq = self.max_freq.get()
        start = self.segment_start.get()
        end = self.segment_end.get()
        
        # Phân tích
        peaks, heights = AudioAnalyzer.detect_peaks(data, sr, threshold, min_distance)
        all_segments = AudioAnalyzer.extract_segments(data, sr, peaks, pre_peak, duration)
        self.total_segments = len(all_segments)
        
        # Cập nhật spinbox range
        self.start_spinbox.config(to=max(0, self.total_segments - 1))
        self.end_spinbox.config(to=max(0, self.total_segments - 1))
        
        if end == -1:
            end = self.total_segments - 1
        if start > end:
            start, end = end, start
        
        used_segments = get_segments_range(all_segments, start, end)
        
        self.file_data[filepath] = {
            'data': data, 'sr': sr, 'peaks': peaks,
            'peak_heights': heights, 'segments': used_segments,
            'all_segments': all_segments
        }
        
        self.segments_info_label.config(
            text=f"Total: {len(all_segments)} | Selected: {len(used_segments)}"
        )
        
        # Vẽ waveform
        time_axis = np.linspace(0, len(data)/sr, len(data))
        self.line_wave.set_data(time_axis, data)
        self.ax1.set_xlim(0, len(data)/sr)
        y_max = max(np.max(np.abs(data)), 0.1)
        self.ax1.set_ylim(-y_max*1.1, y_max*1.1)
        self.ax1.set_title(f'Waveform: {os.path.basename(filepath)}', fontsize=10)
        self.ax1.grid(True, alpha=0.3)
        
        # Peaks
        if len(peaks) > 0:
            self.peak_scatter.set_offsets(np.column_stack((time_axis[peaks], heights)))
        else:
            self.peak_scatter.set_offsets(np.empty((0, 2)))
        
        # Segments
        for patch in self.segment_patches:
            patch.remove()
        self.segment_patches.clear()
        
        if used_segments:
            colors = plt.cm.tab10(np.linspace(0, 1, min(10, len(used_segments))))
            for i, seg in enumerate(used_segments[:10]):
                color = colors[i % len(colors)]
                patch = self.ax1.axvspan(seg['start_time'], seg['end_time'], alpha=0.15, color=color)
                self.segment_patches.append(patch)
                self.ax1.text((seg['start_time'] + seg['end_time'])/2, y_max * 0.9, 
                             f'{i+1}', color=color, ha='center', fontsize=8)
        
        # FFTs
        for line in self.fft_lines:
            line.remove()
        self.fft_lines.clear()
        
        if used_segments:
            colors = plt.cm.tab10(np.linspace(0, 1, min(10, len(used_segments))))
            for i, seg in enumerate(used_segments[:10]):
                color = colors[i % len(colors)]
                d = seg['data']
                N = len(d)
                window = np.hanning(N)
                fft_amp = np.abs(np.fft.fft(d * window))[:N//2]
                if np.max(fft_amp) > 0:
                    fft_amp = fft_amp / np.max(fft_amp)
                freq_axis = np.fft.fftfreq(N, d=1/sr)[:N//2]
                line, = self.ax2.plot(freq_axis, fft_amp, alpha=0.5, linewidth=1, color=color)
                self.fft_lines.append(line)
        
        self.ax2.set_xlim(0, max_freq)
        self.ax2.set_ylim(0, 1)
        self.ax2.grid(True, alpha=0.3)
        
        self.canvas.draw()
        self.status_var.set(f"Loaded: {os.path.basename(filepath)}")
        
        # Auto add to compare
        self._auto_add(filepath)
    
    def _auto_add(self, filepath):
        """Tự động thêm file vào danh sách so sánh"""
        name = os.path.basename(filepath)
        current = self.selected_listbox.get(0, tk.END)
        
        if name in current:
            return
        
        if len(self.selected_file_paths) >= 5:
            self.status_var.set(f"⚠️ Max 5 files! Can't add {name}")
            return
        
        self.selected_listbox.insert(tk.END, name)
        self.selected_file_paths.append(filepath)
        self.status_var.set(f"✅ Added: {name}")
        
        if self.auto_compare_enabled and len(self.selected_file_paths) >= 2:
            self.run_compare()
    
    def on_selected_click(self, event):
        """Click vào file trong danh sách so sánh"""
        selection = self.selected_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self.selected_file_paths):
            self.view_file(self.selected_file_paths[idx])
    
    def remove_selected_file(self):
        """Xóa file khỏi danh sách so sánh"""
        selection = self.selected_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a file to remove!")
            return
        
        idx = selection[0]
        name = self.selected_listbox.get(idx)
        self.selected_listbox.delete(idx)
        if idx < len(self.selected_file_paths):
            self.selected_file_paths.pop(idx)
        self.status_var.set(f"🗑️ Removed: {name}")
        
        if len(self.selected_file_paths) == 0:
            self._clear_compare_plot()
            self.ax1.clear()
            self.ax1.set_title('Waveform - No file selected', fontsize=10)
            self.ax1.set_xlabel('Time (s)', fontsize=9)
            self.ax1.set_ylabel('Amplitude', fontsize=9)
            self.ax1.grid(True, alpha=0.3)
            self.ax2.clear()
            self.ax2.set_title('Individual FFTs', fontsize=10)
            self.ax2.set_xlabel('Frequency (Hz)', fontsize=9)
            self.ax2.set_ylabel('Magnitude', fontsize=9)
            self.ax2.grid(True, alpha=0.3)
            self.canvas.draw()
            self.current_file_label.config(text="Adjusting: None")
            self.segments_info_label.config(text="Total: 0 | Selected: 0")
    
    def add_to_compare(self):
        """Thêm file đã chọn vào danh sách so sánh"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file!")
            return
        
        for idx in selection:
            if idx < len(self.all_files):
                name = os.path.basename(self.all_files[idx])
                current = self.selected_listbox.get(0, tk.END)
                if name not in current and len(self.selected_file_paths) < 5:
                    self.selected_listbox.insert(tk.END, name)
                    self.selected_file_paths.append(self.all_files[idx])
                    self.status_var.set(f"Added: {name}")
        
        if self.selected_file_paths:
            self.view_file(self.selected_file_paths[0])
            if self.auto_compare_enabled and len(self.selected_file_paths) >= 2:
                self.run_compare()
    
    def select_all_segments(self):
        """Chọn tất cả segments"""
        self.segment_start.set(0)
        self.segment_end.set(self.total_segments - 1 if self.total_segments > 0 else 0)
        self.on_segment_range_change()
    
    def select_range(self, start, end):
        """Chọn khoảng segments"""
        self.segment_start.set(start)
        self.segment_end.set(end)
        self.on_segment_range_change()
    
    def select_last_5(self):
        """Chọn 5 segments cuối cùng"""
        if self.total_segments > 0:
            start = max(0, self.total_segments - 5)
            end = self.total_segments - 1
            self.select_range(start, end)
    
    def on_segment_range_change(self):
        """Khi thay đổi khoảng segment"""
        if self.current_viewing_file:
            if self.current_viewing_file not in self.file_params:
                self.file_params[self.current_viewing_file] = {}
            self.file_params[self.current_viewing_file]['seg_start'] = self.segment_start.get()
            self.file_params[self.current_viewing_file]['seg_end'] = self.segment_end.get()
            self.view_file(self.current_viewing_file)
            self._schedule_auto_compare()
    
    def on_param_change(self, *args):
        """Tham số thay đổi"""
        for label_text, var in [
            ("Threshold:", self.threshold),
            ("Pre-peak (s):", self.pre_peak),
            ("Duration (s):", self.segment_duration),
            ("Min Distance:", self.min_distance),
            ("Max Freq (Hz):", self.max_freq),
        ]:
            if label_text in self.param_labels:
                val = var.get()
                self.param_labels[label_text].config(text=f"{val:.2f}" if val < 1 else f"{val:.0f}")
        
        if self.current_viewing_file:
            if self.current_viewing_file not in self.file_params:
                self.file_params[self.current_viewing_file] = {}
            self.file_params[self.current_viewing_file].update({
                'threshold': self.threshold.get(),
                'pre_peak': self.pre_peak.get(),
                'duration': self.segment_duration.get(),
                'min_distance': self.min_distance.get(),
                'max_freq': self.max_freq.get()
            })
            self.view_file(self.current_viewing_file)
            self._schedule_auto_compare()
    
    def toggle_auto(self):
        """Bật/tắt auto compare"""
        self.auto_compare_enabled = not self.auto_compare_enabled
        self.auto_btn.config(text=f"▶ Auto: {'ON' if self.auto_compare_enabled else 'OFF'}")
        if self.auto_compare_enabled and len(self.selected_file_paths) >= 2:
            self.run_compare()
    
    def _schedule_auto_compare(self):
        """Lên lịch auto compare với debounce"""
        if not self.auto_compare_enabled or len(self.selected_file_paths) < 2:
            return
        if self._update_timer:
            self._update_timer.cancel()
        self._update_timer = threading.Timer(0.3, self.run_compare)
        self._update_timer.daemon = True
        self._update_timer.start()
    
    def run_compare(self):
        """So sánh các file đã chọn"""
        if self._is_updating or len(self.selected_file_paths) < 2:
            return
        self.status_var.set("Comparing...")
        thread = threading.Thread(target=self._run_compare)
        thread.daemon = True
        thread.start()
    
    def _run_compare(self):
        """Chạy so sánh"""
        self._is_updating = True
        try:
            for line in self.compare_lines:
                line.remove()
            self.compare_lines.clear()
            for peak in self.compare_peaks:
                peak.remove()
            self.compare_peaks.clear()
            
            self.ax3.clear()
            self.ax3.set_title('Average FFT Comparison', fontsize=10)
            self.ax3.set_xlabel('Frequency (Hz)', fontsize=9)
            self.ax3.set_ylabel('Magnitude', fontsize=9)
            self.ax3.grid(True, alpha=0.3)
            
            max_freq = self.max_freq.get()
            results = []
            
            for i, filepath in enumerate(self.selected_file_paths):
                if filepath in self.file_params:
                    p = self.file_params[filepath]
                    threshold = p.get('threshold', 0.1)
                    pre_peak = p.get('pre_peak', 0.05)
                    duration = p.get('duration', 0.1)
                    min_distance = p.get('min_distance', 0.1)
                    start = p.get('seg_start', 0)
                    end = p.get('seg_end', 0)
                else:
                    threshold = self.threshold.get()
                    pre_peak = self.pre_peak.get()
                    duration = self.segment_duration.get()
                    min_distance = self.min_distance.get()
                    start = self.segment_start.get()
                    end = self.segment_end.get()
                
                if filepath not in self.file_data:
                    data, sr, _ = load_audio(filepath)
                    if data is None:
                        continue
                    peaks, heights = AudioAnalyzer.detect_peaks(data, sr, threshold, min_distance)
                    all_segments = AudioAnalyzer.extract_segments(data, sr, peaks, pre_peak, duration)
                    if end == -1:
                        end = len(all_segments) - 1
                    if start > end:
                        start, end = end, start
                    used = get_segments_range(all_segments, start, end)
                    self.file_data[filepath] = {
                        'data': data, 'sr': sr, 'segments': used,
                        'all_segments': all_segments
                    }
                
                data = self.file_data[filepath]['data']
                sr = self.file_data[filepath]['sr']
                segments = self.file_data[filepath]['segments']
                
                if not segments:
                    continue
                
                freqs, avg_fft, _ = AudioAnalyzer.compute_fft(segments, sr, max_freq)
                if freqs is None:
                    continue
                
                color = self.colors[i % len(self.colors)]
                name = os.path.basename(filepath)
                
                line, = self.ax3.plot(freqs, avg_fft, linewidth=2, label=name, color=color)
                self.compare_lines.append(line)
                
                peak_idx = np.argmax(avg_fft)
                peak_freq = freqs[peak_idx]
                peak_val = avg_fft[peak_idx]
                scatter = self.ax3.scatter([peak_freq], [peak_val], color=color, s=50)
                self.compare_peaks.append(scatter)
                self.ax3.text(peak_freq, peak_val + 0.05, f'{peak_freq:.0f}Hz', 
                            fontsize=7, ha='center')
                
                results.append({'file': name, 'peak_freq': peak_freq})
            
            self.parent.after(0, self._update_compare, results)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.parent.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
        finally:
            self._is_updating = False
    
    def _update_compare(self, results):
        """Cập nhật UI sau so sánh"""
        if not results:
            return
        self.ax3.legend(loc='upper right', fontsize=7)
        self.ax3.set_xlim(0, self.max_freq.get())
        self.ax3.set_ylim(0, 1.1)
        self.canvas.draw()
        self.info_text.delete('1.0', tk.END)
        for r in results:
            self.info_text.insert(tk.END, f"{r['file']}: Peak={r['peak_freq']:.0f}Hz\n")
        self.status_var.set(f"Compared {len(results)} files")
    
    def _clear_compare_plot(self):
        """Xóa plot so sánh"""
        for line in self.compare_lines:
            line.remove()
        self.compare_lines.clear()
        for peak in self.compare_peaks:
            peak.remove()
        self.compare_peaks.clear()
        self.ax3.clear()
        self.ax3.set_title('Average FFT Comparison', fontsize=10)
        self.ax3.set_xlabel('Frequency (Hz)', fontsize=9)
        self.ax3.set_ylabel('Magnitude', fontsize=9)
        self.ax3.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def clear_compare(self):
        """Xóa danh sách so sánh"""
        self.selected_listbox.delete(0, tk.END)
        self.selected_file_paths = []
        self._clear_compare_plot()
        self.ax1.clear()
        self.ax1.set_title('Waveform - No file selected', fontsize=10)
        self.ax1.set_xlabel('Time (s)', fontsize=9)
        self.ax1.set_ylabel('Amplitude', fontsize=9)
        self.ax1.grid(True, alpha=0.3)
        self.ax2.clear()
        self.ax2.set_title('Individual FFTs', fontsize=10)
        self.ax2.set_xlabel('Frequency (Hz)', fontsize=9)
        self.ax2.set_ylabel('Magnitude', fontsize=9)
        self.ax2.grid(True, alpha=0.3)
        self.canvas.draw()
        self.current_file_label.config(text="Adjusting: None")
        self.segments_info_label.config(text="Total: 0 | Selected: 0")
        self.status_var.set("Cleared all")
    
    def export_all_segments(self):
        """Export tất cả segments thành WAV"""
        if not self.selected_file_paths:
            messagebox.showwarning("Warning", "No files!")
            return
        custom = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")],
                                             initialfile="exported_segments")
        if not custom:
            return
        base = os.path.splitext(custom)[0]
        output = os.path.join(os.getcwd(), "processing_Data")
        os.makedirs(output, exist_ok=True)
        total = 0
        for fp in self.selected_file_paths:
            if fp in self.file_data:
                segs = self.file_data[fp]['segments']
                sr = self.file_data[fp]['sr']
                if segs:
                    fbase = os.path.splitext(os.path.basename(fp))[0]
                    saved = save_segments_to_wav(segs, sr, output, f"{base}_{fbase}", f"{base}_{fbase}")
                    total += len(saved)
        if total > 0:
            messagebox.showinfo("Success", f"Saved {total} segments to {output}")
        else:
            messagebox.showwarning("Warning", "No segments to export!")
    
    def export_results(self):
        """Export CSV kết quả so sánh"""
        if not self.selected_file_paths:
            messagebox.showwarning("Warning", "No results!")
            return
        csv = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not csv:
            return
        with open(csv, 'w') as f:
            f.write("File,PeakFreq,NumSegments\n")
            for fp in self.selected_file_paths:
                if fp in self.file_data:
                    segs = self.file_data[fp]['segments']
                    if segs:
                        freqs, avg, _ = AudioAnalyzer.compute_fft(segs, self.file_data[fp]['sr'], self.max_freq.get())
                        if freqs is not None:
                            peak = freqs[np.argmax(avg)]
                            f.write(f"{os.path.basename(fp)},{peak:.1f},{len(segs)}\n")
        messagebox.showinfo("Success", f"Saved to {csv}")