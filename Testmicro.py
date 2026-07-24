import sys
import serial
import threading
import wave
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import serial.tools.list_ports
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

class AudioStreamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32-S3 Audio Streamer - NVS Config")
        self.root.geometry("1100x750")
        
        self.serial_port = None
        self.is_connected = False
        self.is_recording = False  # Đổi từ is_streaming thành is_recording
        self.audio_data = bytearray()
        self.sample_rate = 16000
        self.display_seconds = 2
        self.update_interval = 50
        self.last_data_size = 0
        
        self.current_config = {}
        self.default_config = {
            'sample_rate': 16000,
            'bclk_pin': 11,
            'ws_pin': 10,
            'data_pin': 9,
            'buffer_samples': 512,
            'dma_buf_count': 8,
            'bits_per_sample': 32,
            'channel_format': 0,
            'use_apll': False
        }
        
        self.setup_ui()
        self.scan_ports()
        self.update_timer = None
        self.read_thread = None
        self.running = False
        
    def setup_ui(self):
        # ===== PANEL CHÍNH =====
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ===== PANEL TRÁI: ĐIỀU KHIỂN =====
        left_frame = ttk.Frame(main_panel)
        main_panel.add(left_frame, weight=1)
        
        # --- Connection ---
        conn_frame = ttk.LabelFrame(left_frame, text="Connection", padding=10)
        conn_frame.pack(fill=tk.X, pady=5)
        
        port_row = ttk.Frame(conn_frame)
        port_row.pack(fill=tk.X, pady=2)
        ttk.Label(port_row, text="Port:").pack(side=tk.LEFT, padx=5)
        self.port_combo = ttk.Combobox(port_row, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(port_row, text="Refresh", command=self.scan_ports).pack(side=tk.LEFT, padx=5)
        
        btn_row = ttk.Frame(conn_frame)
        btn_row.pack(fill=tk.X, pady=5)
        self.connect_btn = ttk.Button(btn_row, text="Connect", command=self.toggle_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(btn_row, text="Not connected")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # --- Controls (Đã đổi) ---
        ctrl_frame = ttk.LabelFrame(left_frame, text="Recording Control", padding=10)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        ctrl_row = ttk.Frame(ctrl_frame)
        ctrl_row.pack(pady=5)
        
        # ✅ Đổi thành nút RECORD
        self.record_btn = ttk.Button(ctrl_row, text="🔴 Record", command=self.toggle_record, state=tk.DISABLED)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(ctrl_row, text="💾 Save WAV", command=self.save_audio, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(ctrl_row, text="🗑️ Clear", command=self.clear_data, state=tk.DISABLED)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # --- Status ---
        status_frame = ttk.LabelFrame(left_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.rec_label = ttk.Label(status_frame, text="⚪ Idle")
        self.rec_label.pack(anchor=tk.W, pady=2)
        self.data_label = ttk.Label(status_frame, text="Data: 0 bytes")
        self.data_label.pack(anchor=tk.W, pady=2)
        self.sample_label = ttk.Label(status_frame, text="Samples: 0")
        self.sample_label.pack(anchor=tk.W, pady=2)
        
        self.debug_label = ttk.Label(status_frame, text="Debug: Waiting for data...")
        self.debug_label.pack(anchor=tk.W, pady=2)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # --- NVS Config ---
        config_frame = ttk.LabelFrame(left_frame, text="NVS Configuration", padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        config_canvas = tk.Canvas(config_frame)
        config_scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=config_canvas.yview)
        config_inner = ttk.Frame(config_canvas)
        
        config_canvas.configure(yscrollcommand=config_scrollbar.set)
        config_canvas.pack(side="left", fill="both", expand=True)
        config_scrollbar.pack(side="right", fill="y")
        
        config_canvas.create_window((0, 0), window=config_inner, anchor="nw")
        config_inner.bind("<Configure>", lambda e: config_canvas.configure(scrollregion=config_canvas.bbox("all")))
        
        # Config fields
        self.config_vars = {}
        config_fields = [
            ('sample_rate', 'Sample Rate (Hz)', 16000, 8000, 96000),
            ('bclk_pin', 'BCLK Pin', 11, 0, 39),
            ('ws_pin', 'WS Pin', 10, 0, 39),
            ('data_pin', 'DATA Pin', 9, 0, 39),
            ('buffer_samples', 'Buffer Samples', 512, 64, 1024),
            ('dma_buf_count', 'DMA Buffers', 8, 2, 16),
            ('bits_per_sample', 'Bits/Sample', 32, 16, 32),
            ('channel_format', 'Channel (0=Mono,1=Stereo)', 0, 0, 1),
            ('use_apll', 'Use APLL', False, None, None)
        ]
        
        for idx, (key, label, default, min_val, max_val) in enumerate(config_fields):
            row = ttk.Frame(config_inner)
            row.pack(fill=tk.X, pady=2)
            
            ttk.Label(row, text=label, width=20).pack(side=tk.LEFT, padx=5)
            
            if key == 'use_apll':
                var = tk.BooleanVar(value=default)
                cb = ttk.Checkbutton(row, variable=var)
                cb.pack(side=tk.LEFT, padx=5)
            elif key == 'channel_format':
                var = tk.StringVar(value=str(default))
                combo = ttk.Combobox(row, textvariable=var, values=['0 (Mono)', '1 (Stereo)'], width=15)
                combo.pack(side=tk.LEFT, padx=5)
            else:
                var = tk.StringVar(value=str(default))
                entry = ttk.Entry(row, textvariable=var, width=10)
                entry.pack(side=tk.LEFT, padx=5)
                
                if min_val is not None and max_val is not None:
                    ttk.Label(row, text=f"({min_val}-{max_val})", font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
            
            self.config_vars[key] = var
        
        # Config buttons
        cfg_btn_row = ttk.Frame(config_inner)
        cfg_btn_row.pack(fill=tk.X, pady=10)
        
        ttk.Button(cfg_btn_row, text="📥 Load from ESP32", command=self.load_config_from_esp).pack(side=tk.LEFT, padx=5)
        ttk.Button(cfg_btn_row, text="📤 Send to ESP32", command=self.send_config_to_esp).pack(side=tk.LEFT, padx=5)
        ttk.Button(cfg_btn_row, text="🔄 Reset Default", command=self.reset_default_config).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(cfg_btn_row, text="(ESP32 sẽ restart)", font=('Arial', 8, 'italic')).pack(side=tk.LEFT, padx=10)
        
        # ===== PANEL PHẢI: GRAPH =====
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=2)
        
        graph_frame = ttk.LabelFrame(right_frame, text="Waveform (Last 2 seconds)", padding=5)
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(8, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Time (samples)')
        self.ax.set_ylabel('Amplitude')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(-32768, 32767)
        self.ax.set_title('⏳ Waiting for data...')
        
        self.line, = self.ax.plot([], [], 'b-', linewidth=0.8)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # ===== CONSOLE LOG =====
        log_frame = ttk.LabelFrame(self.root, text="Console Log", padding=5)
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "time")
        self.log_text.insert(tk.END, f"{msg}\n", level.lower())
        self.log_text.see(tk.END)
        
        self.log_text.tag_config("time", foreground="gray")
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
    
    def scan_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.set(port_list[0])
        self.log(f"Scanned ports: {len(port_list)} found", "INFO")
    
    def toggle_connect(self):
        if self.connect_btn['text'] == "Connect":
            port = self.port_combo.get()
            if not port:
                messagebox.showerror("Error", "Please select a port")
                return
            
            try:
                self.serial_port = serial.Serial(port, 115200, timeout=1)
                self.is_connected = True
                self.connect_btn.config(text="Disconnect")
                self.record_btn.config(state=tk.NORMAL)
                self.status_label.config(text=f"Connected to {port}")
                self.log(f"Connected to {port}", "SUCCESS")
                
                # ✅ BẮT ĐẦU ĐỌC DỮ LIỆU TỰ ĐỘNG
                self.running = True
                self.read_thread = threading.Thread(target=self._read_data)
                self.read_thread.daemon = True
                self.read_thread.start()
                
                # Bắt đầu update graph
                self.start_graph_update()
                
                # Load config từ ESP32
                self.root.after(1000, self.load_config_from_esp)
                
                self.log("Auto-stream started, waveform will appear when data arrives", "INFO")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to connect: {str(e)}")
                self.log(f"Connection error: {str(e)}", "ERROR")
        else:
            # Disconnect
            self.running = False
            self.is_connected = False
            if self.is_recording:
                self.toggle_record()
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
            self.connect_btn.config(text="Connect")
            self.record_btn.config(state=tk.DISABLED)
            self.save_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Disconnected")
            self.stop_graph_update()
            self.log("Disconnected", "WARNING")
    
    def toggle_record(self):
        """Bắt đầu/Dừng ghi âm (chỉ lưu dữ liệu)"""
        if not self.serial_port:
            return
        
        if not self.is_recording:
            # Bắt đầu ghi
            self.is_recording = True
            self.audio_data = bytearray()
            self.last_data_size = 0
            self.record_btn.config(text="⏹ Stop Recording")
            self.save_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.DISABLED)
            self.rec_label.config(text="🔴 Recording...", foreground="red")
            self.progress.start()
            self.log("Recording started", "SUCCESS")
        else:
            # Dừng ghi
            self.is_recording = False
            self.record_btn.config(text="🔴 Record")
            self.save_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.NORMAL)
            self.rec_label.config(text="⚪ Stopped", foreground="black")
            self.progress.stop()
            self.log(f"Recording stopped. Total: {len(self.audio_data)} bytes", "WARNING")
    
    def _read_data(self):
        """Đọc dữ liệu từ ESP32 liên tục"""
        while self.running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        # Kiểm tra nếu là config text
                        if data.startswith(b'BCLK') or data.startswith(b'Sample'):
                            self._parse_config(data)
                        else:
                            # ✅ LƯU DỮ LIỆU VÀO audio_data KHI ĐANG RECORD
                            if self.is_recording:
                                self.audio_data.extend(data)
                                current_size = len(self.audio_data)
                                
                                if current_size - self.last_data_size > 1000:
                                    self.last_data_size = current_size
                                    self.root.after(0, self._update_data_label)
                            
                            # ✅ LUÔN CẬP NHẬT GRAPH (bất kể có record hay không)
                            self.root.after(0, lambda d=data: self._update_graph_data(d))
                            
                            # Cập nhật debug
                            self.root.after(0, lambda: self.debug_label.config(
                                text=f"Debug: Receiving data... ({len(data)} bytes)"
                            ))
                            
            except Exception as e:
                self.log(f"Read error: {e}", "ERROR")
                break
        
        self.log("Read thread stopped", "WARNING")
    
    def _update_graph_data(self, data):
        """Cập nhật dữ liệu cho graph (không cần record)"""
        # Lưu vào buffer tạm để hiển thị
        if not hasattr(self, 'graph_buffer'):
            self.graph_buffer = bytearray()
        
        self.graph_buffer.extend(data)
        
        # Giữ buffer ở mức vừa phải (khoảng 2 giây)
        max_buffer = self.display_seconds * self.sample_rate * 2  # 2 bytes/sample
        if len(self.graph_buffer) > max_buffer * 2:
            self.graph_buffer = self.graph_buffer[-max_buffer:]
    
    def _parse_config(self, data):
        try:
            text = data.decode('utf-8', errors='ignore')
            lines = text.split('\n')
            for line in lines:
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        for var_key in self.config_vars:
                            if var_key.upper() in key.upper():
                                self.config_vars[var_key].set(value)
                                self.log(f"Loaded {var_key}: {value}", "INFO")
        except Exception as e:
            self.log(f"Parse config error: {e}", "ERROR")
    
    def _update_data_label(self):
        data_len = len(self.audio_data)
        self.data_label.config(text=f"Data: {data_len} bytes")
        samples = data_len // 2
        self.sample_label.config(text=f"Samples: {samples}")
    
    def load_config_from_esp(self):
        if not self.serial_port:
            return
        
        try:
            self.serial_port.write(b'SHOW\n')
            time.sleep(0.3)
            self.log("Sent SHOW command to ESP32", "INFO")
        except Exception as e:
            self.log(f"Error sending SHOW: {e}", "ERROR")
    
    def send_config_to_esp(self):
        if not self.serial_port:
            messagebox.showwarning("Warning", "Not connected!")
            return
        
        try:
            commands = []
            config_map = {
                'sample_rate': 'SR',
                'bclk_pin': 'BCLK',
                'ws_pin': 'WS',
                'data_pin': 'DATA',
                'buffer_samples': 'BUF',
                'dma_buf_count': 'DMA'
            }
            
            for key, cmd in config_map.items():
                if key in self.config_vars:
                    val = self.config_vars[key].get()
                    if val:
                        commands.append(f"{cmd}={val}")
            
            for cmd in commands:
                self.serial_port.write(f"{cmd}\n".encode())
                time.sleep(0.2)
                self.log(f"Sent: {cmd}", "INFO")
            
            self.serial_port.write(b'SAVE\n')
            time.sleep(0.5)
            self.log("Config sent and saved to NVS", "SUCCESS")
            messagebox.showinfo("Success", "Config sent to ESP32!\nESP32 will restart to apply changes.")
            
        except Exception as e:
            self.log(f"Error sending config: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to send config: {str(e)}")
    
    def reset_default_config(self):
        for key, default_val in self.default_config.items():
            if key in self.config_vars:
                self.config_vars[key].set(str(default_val) if not isinstance(default_val, bool) else default_val)
        self.log("Config reset to default", "INFO")
        
        if self.serial_port:
            try:
                self.serial_port.write(b'RESET\n')
                self.log("Sent RESET command", "WARNING")
                messagebox.showinfo("Reset", "ESP32 will restart with default config!")
            except Exception as e:
                self.log(f"Error sending RESET: {e}", "ERROR")
    
    def save_audio(self):
        if len(self.audio_data) == 0:
            messagebox.showwarning("Warning", "No audio data to save!")
            return
        
        audio_data = self.audio_data
        if len(audio_data) % 2 != 0:
            audio_data = audio_data[:-1]
        
        if len(audio_data) == 0:
            messagebox.showwarning("Warning", "No data after trimming!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"recording_{timestamp}.wav"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
            initialfile=default_name
        )
        
        if not file_path:
            return
        
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            with wave.open(file_path, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(audio_array.tobytes())
            
            self.log(f"Saved: {file_path} ({len(audio_array)} samples)", "SUCCESS")
            messagebox.showinfo("Success", f"Saved: {file_path}\nSamples: {len(audio_array)}")
            
        except Exception as e:
            self.log(f"Save error: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def clear_data(self):
        self.audio_data = bytearray()
        self.last_data_size = 0
        self._update_data_label()
        self.graph_buffer = bytearray()  # Xóa graph buffer
        self.clear_graph()
        self.debug_label.config(text="Debug: Data cleared")
        self.log("Data cleared", "INFO")
    
    def start_graph_update(self):
        self.update_timer = self.root.after(self.update_interval, self.update_graph)
    
    def stop_graph_update(self):
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
            self.update_timer = None
    
    def update_graph(self):
        """Cập nhật waveform từ graph_buffer"""
        if not hasattr(self, 'graph_buffer') or len(self.graph_buffer) < 2:
            self.update_timer = self.root.after(self.update_interval, self.update_graph)
            return
        
        data = self.graph_buffer
        if len(data) % 2 != 0:
            data = data[:-1]
        
        if len(data) < 2:
            self.update_timer = self.root.after(self.update_interval, self.update_graph)
            return
        
        try:
            audio_array = np.frombuffer(data, dtype=np.int16)
            audio_array = np.clip(audio_array, -32768, 32767)
            
            display_samples = self.display_seconds * 16000
            if len(audio_array) > display_samples:
                audio_array = audio_array[-display_samples:]
            
            x_data = np.arange(len(audio_array))
            self.line.set_data(x_data, audio_array)
            self.ax.set_xlim(0, max(len(audio_array), 100))
            
            if len(audio_array) > 0:
                max_val = int(np.max(np.abs(audio_array))) if len(audio_array) > 0 else 100
                if max_val < 100:
                    max_val = 100
                self.ax.set_ylim(-max_val * 1.2, max_val * 1.2)
            
            # Cập nhật title
            if self.is_recording:
                self.ax.set_title('🔴 RECORDING', color='red')
            else:
                self.ax.set_title('🎵 Live Stream (Preview)', color='blue')
            
            self.fig.tight_layout()
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"Graph error: {e}")
        
        self.update_timer = self.root.after(self.update_interval, self.update_graph)
    
    def clear_graph(self):
        self.line.set_data([], [])
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(-32768, 32767)
        self.ax.set_title('⏳ Waiting for data...')
        self.fig.tight_layout()
        self.canvas.draw_idle()

# ============================================
# CHẠY ỨNG DỤNG
# ============================================
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioStreamerApp(root)
    root.mainloop()