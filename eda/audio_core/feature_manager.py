"""
Quản lý đặc trưng âm thanh - Lưu và cập nhật CSV
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


class FeatureManager:
    """Quản lý trích xuất và lưu đặc trưng"""
    
    def __init__(self, csv_path=None):
        # Nếu không chỉ định, lưu ở thư mục hiện tại
        if csv_path is None:
            csv_path = os.path.join(os.getcwd(), "audio_features.csv")
        self.csv_path = csv_path
        self.columns = [
            'file_name', 'tool_type', 
            # 'segment_index',
            'peak_freq', 
            # 'peak_mag',
            'spectral_centroid', 
            'spectral_bandwidth',
            'spectral_rolloff', 'spectral_spread',
            'spectral_skewness', 'spectral_kurtosis',
            'rms_energy', 'zero_crossing_rate',
            'peak_to_peak', 'energy',
            'duration', 
            'start_time', 
            'end_time',
            # 'num_segments',
            # 'extract_date'
        ]
        self.df = self._load_or_create()
        self.last_saved_path = None
    
    def _load_or_create(self):
        """Load CSV nếu tồn tại, hoặc tạo mới"""
        if os.path.exists(self.csv_path):
            try:
                df = pd.read_csv(self.csv_path)
                print(f"✅ Loaded existing features: {len(df)} rows from {self.csv_path}")
                return df
            except Exception as e:
                print(f"⚠️ Error loading CSV: {e}")
                return pd.DataFrame(columns=self.columns)
        else:
            print(f"📁 Creating new feature database at: {self.csv_path}")
            return pd.DataFrame(columns=self.columns)
    
    def add_features(self, file_name, tool_type, segment_features):
        """
        Thêm đặc trưng của một file vào database
        """
        new_rows = []
        num_segments = len(segment_features)
        
        for seg in segment_features:
            row = {
                'file_name': file_name,
                'tool_type': tool_type,
                # 'segment_index': seg.get('segment_index', 0),
                'peak_freq': seg.get('peak_freq', 0),
                'peak_mag': seg.get('peak_mag', 0),
                'spectral_centroid': seg.get('spectral_centroid', 0),
                'spectral_bandwidth': seg.get('spectral_bandwidth', 0),
                'spectral_rolloff': seg.get('spectral_rolloff', 0),
                'spectral_spread': seg.get('spectral_spread', 0),
                'spectral_skewness': seg.get('spectral_skewness', 0),
                'spectral_kurtosis': seg.get('spectral_kurtosis', 0),
                'rms_energy': seg.get('rms_energy', 0),
                'zero_crossing_rate': seg.get('zero_crossing_rate', 0),
                'peak_to_peak': seg.get('peak_to_peak', 0),
                'energy': seg.get('energy', 0),
                'duration': seg.get('duration', 0),
                'start_time': seg.get('start_time', 0),
                'end_time': seg.get('end_time', 0),
                # 'num_segments': num_segments,
                # 'extract_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            new_rows.append(row)
        
        new_df = pd.DataFrame(new_rows)
        self.df = pd.concat([self.df, new_df], ignore_index=True)
        self.save()
        
        return len(new_rows)
    
    def add_aggregated_features(self, file_name, tool_type, agg_features):
        """Thêm đặc trưng tổng hợp của file"""
        row = {
            'file_name': file_name,
            'tool_type': tool_type,
            # 'segment_index': -1,
            # 'num_segments': 0,
            # 'extract_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        for key, value in agg_features.items():
            if key in self.columns:
                row[key] = value
        
        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)
        self.save()
    
    def save(self, custom_path=None):
        """Lưu dataframe vào CSV"""
        if custom_path:
            self.csv_path = custom_path
        
        # Đảm bảo thư mục tồn tại
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        
        self.df.to_csv(self.csv_path, index=False)
        self.last_saved_path = self.csv_path
        print(f"✅ Saved {len(self.df)} rows to {self.csv_path}")
        return self.csv_path
    
    def get_all_files(self):
        """Lấy danh sách tất cả file đã có trong database"""
        if len(self.df) == 0:
            return []
        return self.df['file_name'].unique().tolist()
    
    def get_file_features(self, file_name):
        """Lấy đặc trưng của một file cụ thể"""
        return self.df[self.df['file_name'] == file_name]
    
    def get_tool_features(self, tool_type):
        """Lấy đặc trưng của một loại đầu gõ"""
        return self.df[self.df['tool_type'] == tool_type]
    
    def get_summary_stats(self, group_by='tool_type'):
        """Thống kê tóm tắt theo nhóm"""
        if len(self.df) == 0:
            return pd.DataFrame()
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        summary = self.df.groupby(group_by)[numeric_cols].agg([
            'mean', 'std', 'min', 'max', 'count'
        ])
        return summary
    
    def check_duplicate(self, file_name):
        """Kiểm tra file đã tồn tại trong database chưa"""
        return file_name in self.get_all_files()
    
    def get_dataframe(self):
        """Trả về dataframe hiện tại"""
        return self.df

    # ===== THÊM VÀO CUỐI FILE =====

    def save_fft_points(self, file_name, tool_type, label, freq_points, 
                        min_freq, max_freq, num_points=512):
        """
        Lưu các điểm FFT đã cắt vào CSV
        
        Parameters:
        - file_name: tên file
        - tool_type: loại đầu gõ
        - label: nhãn (0, 1, 2, ...)
        - freq_points: mảng biên độ FFT (num_points điểm)
        - min_freq: tần số bắt đầu
        - max_freq: tần số kết thúc
        - num_points: số điểm
        
        Returns:
        - str: đường dẫn file đã lưu
        """
        # Tên file csv
        fft_path = self.csv_path.replace('.csv', f'_fft_points_{min_freq:.0f}_{max_freq:.0f}Hz_{num_points}pts.csv')
        
        # Tạo tên cột
        columns = ['file_name', 'tool_type', 'label']
        columns += [f'freq_{i}' for i in range(num_points)]
        
        # Kiểm tra file đã tồn tại chưa
        if os.path.exists(fft_path):
            df_existing = pd.read_csv(fft_path)
        else:
            df_existing = pd.DataFrame(columns=columns)
        
        # Tạo row dữ liệu mới
        row = [file_name, tool_type, label]
        row += list(freq_points)
        
        # Thêm vào dataframe
        new_row = pd.DataFrame([row], columns=columns)
        df_new = pd.concat([df_existing, new_row], ignore_index=True)
        
        # Lưu file
        df_new.to_csv(fft_path, index=False)
        
        return fft_path

    def save_multiple_fft_points(self, data_list, min_freq, max_freq, num_points=512):
        """
        Lưu nhiều file FFT points vào CSV
        
        Parameters:
        - data_list: list các dict {file_name, tool_type, label, freq_points}
        - min_freq: tần số bắt đầu
        - max_freq: tần số kết thúc
        - num_points: số điểm
        
        Returns:
        - str: đường dẫn file đã lưu
        """
        fft_path = self.csv_path.replace('.csv', f'_fft_points_{min_freq:.0f}_{max_freq:.0f}Hz_{num_points}pts.csv')
        
        columns = ['file_name', 'tool_type', 'label']
        columns += [f'freq_{i}' for i in range(num_points)]
        
        df = pd.DataFrame(columns=columns)
        
        for item in data_list:
            row = [item['file_name'], item['tool_type'], item['label']]
            row += list(item['freq_points'])
            df.loc[len(df)] = row
        
        df.to_csv(fft_path, index=False)
        return fft_path