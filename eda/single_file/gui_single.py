"""
Giao diện Single File - Rút gọn, đầy đủ chức năng
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


class SingleFileGUI:
    """Giao diện Single File - Rút gọn"""
    
    def __init__(self, parent, wav_file=None):
        self.parent = parent
        self.wav_path = wav_file or "Recording 4.wav"
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Data
        self.data = None
        self.samplerate = None
        self.time_axis = None
        self.total_time = 0
        self.length = 0
        
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
        
        # Results
        self.peak_times = []
        self.peak_values = []
        self.all_segments = []
        self.used_segments = []
        self.avg_freq = None
        self.avg_fft = None
        self.peaks_fft = []
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = None
        
        self.setup_ui()
        self.load_audio_file()
        self.parent.after(500, self.run_analysis)
    
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
        ttk.Label(scroll_frame, text="📊 Single File", font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=5)
        
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
        self.file_label = ttk.Label(info_frame, text=os.path.basename(self.wav_path), font=('Arial', 10, 'bold'))
        self.file_label.pack(anchor=tk.W)
        self.file_info_label = ttk.Label(info_frame, text="", font=('Arial', 9))
        self.file_info_label.pack(anchor=tk.W)
        
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
        
        # 5. Export
        export_frame = ttk.LabelFrame(scroll_frame, text="💾 Export", padding=5)
        export_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(export_frame, text="📁 Export WAV", 
                  command=self.export_segments_to_wav).pack(fill=tk.X, pady=1)
        ttk.Button(export_frame, text="📊 Extract Features", 
                  command=self.extract_and_save_features).pack(fill=tk.X, pady=1)
        ttk.Button(export_frame, text="💾 Export CSV", 
                  command=self.export_results).pack(fill=tk.X, pady=1)
        
        # 6. Results
        result_frame = ttk.LabelFrame(scroll_frame, text="📊 Results", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.info_text = tk.Text(result_frame, height=4, font=('Consolas', 9),
                                bg='#1e1e1e', fg='#d4d4d4')
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # === PANEL PHẢI ===
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=3)
        
        # Figure lớn hơn để các subplot có không gian
        self.fig = Figure(figsize=(10, 10), dpi=100)
        
        # Subplot 1: Waveform
        self.ax1 = self.fig.add_subplot(311)
        self.ax1.set_title('Waveform', fontsize=10)
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
        
        # Subplot 3: Average FFT
        self.ax3 = self.fig.add_subplot(313)
        self.ax3.set_title('Average FFT', fontsize=10)
        self.ax3.set_xlabel('Frequency (Hz)', fontsize=9)
        self.ax3.set_ylabel('Magnitude', fontsize=9)
        self.ax3.grid(True, alpha=0.3)
        self.ax3.tick_params(labelsize=8)
        self.avg_line, = self.ax3.plot([], [], 'r-', linewidth=2)
        self.peak_fft_scatter = self.ax3.scatter([], [], color='green', s=40)
        
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
        
        self.refresh_file_list()
    
    # === CÁC HÀM XỬ LÝ ===
    
    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        audio_files = get_audio_files(self.current_dir)
        if not audio_files:
            self.file_listbox.insert(tk.END, "⚠️ No audio files")
            return
        for i, f in enumerate(audio_files):
            self.file_listbox.insert(tk.END, format_file_display(f, i))
            if os.path.basename(f) == os.path.basename(self.wav_path):
                self.file_listbox.selection_set(i)
        self.update_status(f"Found {len(audio_files)} files")
    
    def update_status(self, text):
        self.status_var.set(text)
        if self.status_bar:
            self.status_bar.config(text=text)
    
    def load_audio_file(self, filepath=None):
        if filepath:
            self.wav_path = filepath
        data, sr, _ = load_audio(self.wav_path)
        if data is not None:
            self.data = data
            self.samplerate = sr
            self.length = len(data)
            self.time_axis = np.linspace(0, self.length/sr, self.length)
            self.total_time = self.length/sr
            self.file_info_label.config(text=f"Rate: {sr} Hz | Duration: {self.total_time:.2f}s")
        else:
            self._create_dummy_data()
    
    def _create_dummy_data(self):
        self.samplerate = 16000
        self.data = np.random.randn(16000*3).astype(np.float32)*0.1
        self.length = len(self.data)
        self.time_axis = np.linspace(0, self.length/self.samplerate, self.length)
        self.total_time = self.length/self.samplerate
    
    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        audio_files = get_audio_files(self.current_dir)
        if index < len(audio_files):
            self.load_selected_file(audio_files[index])
    
    def load_selected_file(self, filepath):
        self.update_status(f"Loading: {os.path.basename(filepath)}...")
        self.wav_path = filepath
        self.load_audio_file()
        self.file_label.config(text=os.path.basename(filepath))
        self.line_wave.set_data(self.time_axis, self.data)
        self.ax1.set_xlim(0, self.total_time)
        y_max = max(np.max(np.abs(self.data)), 0.1)
        self.ax1.set_ylim(-y_max*1.1, y_max*1.1)
        self._clear_lines()
        self.canvas.draw()
        self.parent.after(300, self.run_analysis)
    
    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio files", "*.wav *.WAV *.mp3 *.MP3 *.m4a *.M4A *.flac *.FLAC *.ogg *.OGG")]
        )
        if filepath:
            self.load_selected_file(filepath)
            self.refresh_file_list()
    
    def _clear_lines(self):
        for line in self.fft_lines:
            line.remove()
        self.fft_lines.clear()
        self.avg_line.set_data([], [])
        self.peak_fft_scatter.set_offsets(np.empty((0, 2)))
        self._clear_segment_patches()
    
    def _clear_segment_patches(self):
        for patch in self.segment_patches:
            patch.remove()
        self.segment_patches.clear()
    
    def on_param_change(self, *args):
        self._update_labels()
        if self.data is not None:
            self.run_analysis()
    
    def _update_labels(self):
        for label_text, var in [
            ("Threshold:", self.threshold),
            ("Pre-peak (s):", self.pre_peak),
            ("Duration (s):", self.segment_duration),
            ("Min Distance:", self.min_distance),
            ("Max Freq (Hz):", self.max_freq),
        ]:
            if label_text in self.param_labels:
                val = var.get()
                self.param_labels[label_text].config(
                    text=f"{val:.2f}" if val < 1 else f"{val:.0f}"
                )
    
    def select_all_segments(self):
        self.segment_start.set(0)
        self.segment_end.set(self.total_segments - 1 if self.total_segments > 0 else 0)
        self.on_segment_range_change()
    
    def select_range(self, start, end):
        self.segment_start.set(start)
        self.segment_end.set(end)
        self.on_segment_range_change()
    
    def select_last_5(self):
        if self.total_segments > 0:
            start = max(0, self.total_segments - 5)
            end = self.total_segments - 1
            self.select_range(start, end)
    
    def on_segment_range_change(self):
        self.run_analysis()
    
    def run_analysis(self):
        if self.data is None:
            return
        self.update_status("Analyzing...")
        thread = threading.Thread(target=self._run_analysis)
        thread.daemon = True
        thread.start()
    
    def _run_analysis(self):
        try:
            threshold = self.threshold.get()
            pre_peak = self.pre_peak.get()
            duration = self.segment_duration.get()
            min_distance = self.min_distance.get()
            max_freq = self.max_freq.get()
            
            start_idx = self.segment_start.get()
            end_idx = self.segment_end.get()
            
            peaks, heights = AudioAnalyzer.detect_peaks(self.data, self.samplerate, threshold, min_distance)
            self.peak_times = self.time_axis[peaks]
            self.peak_values = heights
            
            all_segments = AudioAnalyzer.extract_segments(self.data, self.samplerate, peaks, pre_peak, duration)
            self.all_segments = all_segments
            self.total_segments = len(all_segments)
            
            if end_idx == -1:
                end_idx = self.total_segments - 1
            if start_idx > end_idx:
                start_idx, end_idx = end_idx, start_idx
            
            self.used_segments = get_segments_range(all_segments, start_idx, end_idx)
            self.segments_info_label.config(
                text=f"Total: {len(all_segments)} | Selected: {len(self.used_segments)}"
            )
            
            if self.used_segments:
                freqs, avg_fft, fft_peaks = AudioAnalyzer.compute_fft(self.used_segments, self.samplerate, max_freq)
                self.avg_freq = freqs
                self.avg_fft = avg_fft
                self.peaks_fft = fft_peaks
            
            self.parent.after(0, self._update_graphs, max_freq)
            self.parent.after(0, self._update_info)
            self.parent.after(0, lambda: self.update_status(f"Done - {len(self.peak_times)} peaks"))
            
        except Exception as e:
            self.parent.after(0, lambda: self.update_status(f"Error: {str(e)}"))
    
    def _update_graphs(self, max_freq):
        self.line_wave.set_data(self.time_axis, self.data)
        self.ax1.set_xlim(0, self.total_time)
        y_max = max(np.max(np.abs(self.data)), 0.1)
        self.ax1.set_ylim(-y_max*1.1, y_max*1.1)
        
        if len(self.peak_times) > 0:
            self.peak_scatter.set_offsets(np.column_stack((self.peak_times, self.peak_values)))
        else:
            self.peak_scatter.set_offsets(np.empty((0, 2)))
        
        self._clear_segment_patches()
        if self.used_segments:
            colors = plt.cm.tab10(np.linspace(0, 1, min(10, len(self.used_segments))))
            for i, seg in enumerate(self.used_segments[:10]):
                color = colors[i % len(colors)]
                patch = self.ax1.axvspan(seg['start_time'], seg['end_time'], alpha=0.15, color=color)
                self.segment_patches.append(patch)
                self.ax1.text((seg['start_time'] + seg['end_time'])/2, y_max * 0.9, 
                             f'{i+1}', color=color, ha='center', fontsize=8)
        
        for line in self.fft_lines:
            line.remove()
        self.fft_lines.clear()
        
        if self.used_segments:
            colors = plt.cm.tab10(np.linspace(0, 1, min(10, len(self.used_segments))))
            for i, seg in enumerate(self.used_segments[:10]):
                color = colors[i % len(colors)]
                data = seg['data']
                N = len(data)
                fft_amp = np.abs(np.fft.fft(data * np.hanning(N)))[:N//2]
                if np.max(fft_amp) > 0:
                    fft_amp = fft_amp / np.max(fft_amp)
                freq_axis = np.fft.fftfreq(N, d=1/self.samplerate)[:N//2]
                line, = self.ax2.plot(freq_axis, fft_amp, alpha=0.5, linewidth=1, color=color)
                self.fft_lines.append(line)
        
        self.ax2.set_xlim(0, max_freq)
        self.ax2.set_ylim(0, 1)
        
        if self.avg_freq is not None:
            mask = self.avg_freq <= max_freq
            self.avg_line.set_data(self.avg_freq[mask], self.avg_fft[mask])
            valid_peaks = [p for p in self.peaks_fft if p < len(mask) and mask[p]]
            if valid_peaks:
                self.peak_fft_scatter.set_offsets(np.column_stack((self.avg_freq[valid_peaks], self.avg_fft[valid_peaks])))
            self.ax3.set_xlim(0, max_freq)
            self.ax3.set_ylim(0, 1.1)
        
        self.canvas.draw()
    
    def _update_info(self):
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', f"Peaks: {len(self.peak_times)}\n")
        self.info_text.insert(tk.END, f"Segments: {len(self.used_segments)}\n")
        self.info_text.insert(tk.END, f"FFT peaks: {len(self.peaks_fft)}\n")
        if len(self.peaks_fft) > 0:
            self.info_text.insert(tk.END, "Frequencies:\n")
            for idx in self.peaks_fft[:5]:
                if idx < len(self.avg_freq):
                    self.info_text.insert(tk.END, f"  {self.avg_freq[idx]:.0f}Hz\n")
    
    def export_segments_to_wav(self):
        if not self.used_segments:
            messagebox.showwarning("Warning", "No segments!")
            return
        custom_name = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")],
            initialfile=f"{os.path.splitext(os.path.basename(self.wav_path))[0]}_seg"
        )
        if custom_name:
            base_name = os.path.splitext(custom_name)[0]
            output_dir = os.path.join(os.getcwd(), "processing_Data")
            saved = save_segments_to_wav(self.used_segments, self.samplerate, output_dir, 
                                         os.path.basename(base_name), os.path.basename(base_name))
            messagebox.showinfo("Success", f"Saved {len(saved)} files to {output_dir}")
    
    def extract_and_save_features(self):
        if not self.used_segments:
            messagebox.showwarning("Warning", "No segments!")
            return
        tool_type = simpledialog.askstring("Tool Type", "Enter tool type:")
        if not tool_type:
            return
        csv_path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                                filetypes=[("CSV files", "*.csv")],
                                                initialfile="audio_features.csv")
        if not csv_path:
            return
        freqs, avg_fft, _ = AudioAnalyzer.compute_fft(self.used_segments, self.samplerate, self.max_freq.get())
        features = AudioAnalyzer.extract_features_from_segments(self.used_segments, self.samplerate, freqs, avg_fft)
        if not features['segment_features']:
            messagebox.showwarning("Warning", "No features!")
            return
        manager = FeatureManager(csv_path)
        if manager.check_duplicate(os.path.basename(self.wav_path)):
            if not messagebox.askyesno("Duplicate", "Overwrite?"):
                return
            manager.df = manager.df[manager.df['file_name'] != os.path.basename(self.wav_path)]
        num = manager.add_features(os.path.basename(self.wav_path), tool_type, features['segment_features'])
        messagebox.showinfo("Success", f"Saved {num} features to {csv_path}")
    
    def export_results(self):
        if self.avg_freq is None:
            messagebox.showwarning("Warning", "No results!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if file_path:
            mask = self.avg_freq <= self.max_freq.get()
            np.savetxt(file_path, np.column_stack((self.avg_freq[mask], self.avg_fft[mask])),
                      delimiter=',', header='Frequency,Magnitude', comments='')
            self.update_status(f"Exported: {os.path.basename(file_path)}")