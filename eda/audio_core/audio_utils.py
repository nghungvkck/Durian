"""
Hàm tiện ích chung
"""

import os
import glob
import numpy as np
import scipy.io.wavfile as wavfile
from datetime import datetime


SUPPORTED_FORMATS = [
    '.wav', '.WAV', '.wave', 
    '.mp3', '.MP3',
    '.m4a', '.M4A',
    '.flac', '.FLAC',
    '.ogg', '.OGG',
    '.aac', '.AAC'
]


def get_audio_files(directory=None):
    """Lấy danh sách file audio trong thư mục"""
    if directory is None:
        directory = os.getcwd()
    
    audio_files = []
    for ext in SUPPORTED_FORMATS:
        pattern = os.path.join(directory, f"*{ext}")
        audio_files.extend(glob.glob(pattern))
    
    audio_files = list(set(audio_files))
    audio_files.sort(key=os.path.getmtime, reverse=True)
    return audio_files


def get_file_info(filepath):
    """Lấy thông tin file"""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].upper()
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    
    return {
        'filename': filename,
        'ext': ext,
        'size_mb': size_mb,
        'basename': os.path.splitext(filename)[0]
    }


def format_file_display(filepath, index=None):
    """Format tên file để hiển thị trong listbox"""
    info = get_file_info(filepath)
    if index is not None:
        return f"{index+1:2d}. [{info['ext']}] {info['filename']} ({info['size_mb']:.1f} MB)"
    return f"[{info['ext']}] {info['filename']} ({info['size_mb']:.1f} MB)"


def save_segments_to_wav(segments, sr, output_dir="processing_Data", prefix="segment", custom_name=None):
    """
    Lưu các segments thành file .wav với tên tùy chỉnh
    
    Parameters:
    - segments: list các segments
    - sr: sample rate
    - output_dir: thư mục lưu file
    - prefix: tiền tố tên file (mặc định)
    - custom_name: tên file tùy chỉnh (không bao gồm extension)
    
    Returns:
    - list: danh sách đường dẫn file đã lưu
    """
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nếu có tên tùy chỉnh, dùng nó, không thì dùng prefix + timestamp
    base_name = custom_name if custom_name else f"{prefix}_{timestamp}"
    
    for i, seg in enumerate(segments):
        data = seg['data']
        data_int16 = (data * 32767).astype(np.int16)
        
        filename = f"{base_name}_{i+1:03d}.wav"
        filepath = os.path.join(output_dir, filename)
        
        # Kiểm tra nếu file đã tồn tại thì thêm số
        counter = 1
        while os.path.exists(filepath):
            filename = f"{base_name}_{i+1:03d}_{counter}.wav"
            filepath = os.path.join(output_dir, filename)
            counter += 1
        
        wavfile.write(filepath, sr, data_int16)
        saved_files.append(filepath)
    
    return saved_files


def get_selected_segments(all_segments, selected_indices):
    """
    Lấy các segments theo chỉ số được chọn
    
    Parameters:
    - all_segments: list tất cả segments
    - selected_indices: list chỉ số muốn chọn (0-based)
    
    Returns:
    - list: segments đã chọn
    """
    if not selected_indices:
        return all_segments
    
    selected = []
    for idx in selected_indices:
        if 0 <= idx < len(all_segments):
            selected.append(all_segments[idx])
    return selected


def get_segments_range(all_segments, start_idx, end_idx):
    """
    Lấy các segments trong khoảng từ start_idx đến end_idx
    
    Parameters:
    - all_segments: list tất cả segments
    - start_idx: chỉ số bắt đầu (0-based)
    - end_idx: chỉ số kết thúc (0-based, inclusive)
    
    Returns:
    - list: segments đã chọn
    """
    if start_idx < 0:
        start_idx = 0
    if end_idx >= len(all_segments):
        end_idx = len(all_segments) - 1
    if start_idx > end_idx:
        return []
    
    return all_segments[start_idx:end_idx + 1]