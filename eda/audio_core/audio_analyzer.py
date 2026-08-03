"""
Class phân tích âm thanh - Peaks, Segments, FFT, và Feature Extraction
"""

import numpy as np
from scipy.signal import find_peaks
from scipy.interpolate import interp1d


class AudioAnalyzer:
    """Phân tích tín hiệu âm thanh"""
    
    @staticmethod
    def detect_peaks(data, sr, threshold=0.1, min_distance=0.1):
        """
        Phát hiện các đỉnh (peaks) trong tín hiệu
        
        Parameters:
        - data: tín hiệu audio
        - sr: sample rate
        - threshold: ngưỡng phát hiện peak
        - min_distance: khoảng cách tối thiểu giữa các peaks (giây)
        
        Returns:
        - peaks: indices của các peaks
        - peak_heights: biên độ của các peaks
        """
        abs_data = np.abs(data)
        min_dist_samples = int(min_distance * sr)
        peaks, properties = find_peaks(abs_data, height=threshold, distance=min_dist_samples)
        if len(peaks) == 0:
            return np.array([]), np.array([])
        return peaks, properties['peak_heights']
    
    @staticmethod
    def extract_segments(data, sr, peaks, pre_peak=0.05, duration=0.1):
        """
        Trích xuất các đoạn (segments) xung quanh mỗi peak
        
        Parameters:
        - data: tín hiệu audio
        - sr: sample rate
        - peaks: indices của các peaks
        - pre_peak: thời gian trước peak (giây)
        - duration: độ dài segment (giây)
        
        Returns:
        - list segments: mỗi segment là dict với data, start_time, end_time, peak_time
        """
        segments = []
        segment_samples = int(duration * sr)
        pre_samples = int(pre_peak * sr)
        time_axis = np.linspace(0, len(data) / sr, num=len(data))
        
        for peak_idx in peaks:
            start_idx = max(0, peak_idx - pre_samples)
            end_idx = min(len(data), start_idx + segment_samples)
            segment = data[start_idx:end_idx]
            if len(segment) >= 64:
                segments.append({
                    'data': segment,
                    'peak_time': time_axis[peak_idx],
                    'start_time': start_idx / sr,
                    'end_time': end_idx / sr
                })
        return segments
    
    @staticmethod
    def compute_fft(segments, sr, max_freq=None, n_fft=None):
        """
        Tính FFT trung bình từ các segments
        
        Parameters:
        - segments: list segments
        - sr: sample rate
        - max_freq: giới hạn tần số tối đa
        - n_fft: số điểm FFT (zero-padding), nếu None thì dùng len(data)
        
        Returns:
        - freqs: mảng tần số
        - avg_fft: FFT trung bình
        - peaks_fft: indices của các peaks trên FFT
        """
        if not segments:
            return None, None, None
        
        ffts = []
        freq_axes = []
        
        for seg in segments:
            data = seg['data']
            N = len(data)
            window = np.hanning(N)
            data_windowed = data * window
            
            # === NẾU CÓ n_fft, DÙNG ZERO-PADDING ĐỂ TĂNG ĐIỂM ===
            if n_fft is not None and n_fft > N:
                # Zero-padding: thêm số 0 vào cuối tín hiệu
                data_padded = np.zeros(n_fft)
                data_padded[:N] = data_windowed
                fft_amp = np.abs(np.fft.fft(data_padded))[:n_fft//2]
                freq_axis = np.fft.fftfreq(n_fft, d=1/sr)[:n_fft//2]
            else:
                fft_amp = np.abs(np.fft.fft(data_windowed))[:N//2]
                freq_axis = np.fft.fftfreq(N, d=1/sr)[:N//2]
            
            # Chuẩn hóa về [0, 1]
            if np.max(fft_amp) > 0:
                fft_amp = fft_amp / np.max(fft_amp)
            
            ffts.append(fft_amp)
            freq_axes.append(freq_axis)
        
        # Resample về cùng độ dài
        min_len = min(len(f) for f in freq_axes)
        common_freq = freq_axes[0][:min_len]
        resampled = []
        
        for fft_amp, freq in zip(ffts, freq_axes):
            if len(freq) > min_len:
                interp = interp1d(freq, fft_amp, kind='linear', bounds_error=False, fill_value=0)
                resampled.append(interp(common_freq))
            else:
                resampled.append(fft_amp[:min_len])
        
        # Tính FFT trung bình
        avg_fft = np.mean(resampled, axis=0)
        peaks_fft, _ = find_peaks(avg_fft, height=0.1, distance=5)
        
        # Giới hạn tần số
        if max_freq:
            mask = common_freq <= max_freq
            return common_freq[mask], avg_fft[mask], [p for p in peaks_fft if p < len(mask) and mask[p]]
        
        return common_freq, avg_fft, peaks_fft

    # ===== PHẦN TRÍCH XUẤT ĐẶC TRƯNG =====
    
    @staticmethod
    def extract_features_from_segments(segments, sr, freqs=None, avg_fft=None):
        """
        Trích xuất đặc trưng từ các segments đã chọn
        
        Parameters:
        - segments: list các segments đã chọn
        - sr: sample rate
        - freqs: mảng tần số (nếu có)
        - avg_fft: FFT trung bình (nếu có)
        
        Returns:
        - dict: các đặc trưng của từng segment và tổng hợp
        """
        features = {
            'segment_features': [],
            'aggregated': {}
        }
        
        if not segments:
            return features
        
        # 1. Trích xuất đặc trưng cho từng segment
        for i, seg in enumerate(segments):
            data = seg['data']
            N = len(data)
            
            window = np.hanning(N)
            fft_amp = np.abs(np.fft.fft(data * window))[:N//2]
            freq_axis = np.fft.fftfreq(N, d=1/sr)[:N//2]
            
            if np.max(fft_amp) > 0:
                fft_amp = fft_amp / np.max(fft_amp)
            
            seg_features = AudioAnalyzer.extract_single_features(
                freq_axis, fft_amp, data, sr
            )
            seg_features['segment_index'] = i + 1
            seg_features['start_time'] = seg['start_time']
            seg_features['end_time'] = seg['end_time']
            seg_features['duration'] = seg['end_time'] - seg['start_time']
            
            features['segment_features'].append(seg_features)
        
        # 2. Tính đặc trưng tổng hợp
        if features['segment_features']:
            agg = {}
            exclude_keys = ['segment_index', 'start_time', 'end_time']
            
            for key in features['segment_features'][0].keys():
                if key not in exclude_keys:
                    values = [f[key] for f in features['segment_features'] if key in f]
                    if values:
                        agg[f'avg_{key}'] = np.mean(values)
                        agg[f'std_{key}'] = np.std(values)
                        agg[f'min_{key}'] = np.min(values)
                        agg[f'max_{key}'] = np.max(values)
            
            features['aggregated'] = agg
        
        # 3. Nếu có FFT trung bình
        if freqs is not None and avg_fft is not None:
            agg_features = AudioAnalyzer.extract_single_features(freqs, avg_fft, None, sr)
            features['aggregated_fft'] = agg_features
        
        return features

    @staticmethod
    def extract_single_features(freqs, fft_spectrum, data=None, sr=None):
        """
        Trích xuất đặc trưng từ một FFT và dữ liệu tín hiệu
        
        Returns:
        - dict: các đặc trưng
        """
        features = {}
        
        # === Đặc trưng tần số ===
        if len(freqs) > 0 and len(fft_spectrum) > 0:
            # Peak Frequency
            peak_idx = np.argmax(fft_spectrum)
            features['peak_freq'] = freqs[peak_idx]
            features['peak_mag'] = fft_spectrum[peak_idx]
            
            # Spectral Centroid
            if np.sum(fft_spectrum) > 0:
                features['spectral_centroid'] = np.sum(freqs * fft_spectrum) / np.sum(fft_spectrum)
            else:
                features['spectral_centroid'] = 0
            
            # Spectral Bandwidth
            if features['spectral_centroid'] > 0:
                centroid = features['spectral_centroid']
                variance = np.sum(((freqs - centroid) ** 2) * fft_spectrum) / np.sum(fft_spectrum)
                features['spectral_bandwidth'] = np.sqrt(variance)
            else:
                features['spectral_bandwidth'] = 0
            
            # Spectral Rolloff (85%)
            cumsum = np.cumsum(fft_spectrum)
            total = cumsum[-1]
            if total > 0:
                rolloff_idx = np.where(cumsum >= 0.85 * total)[0]
                features['spectral_rolloff'] = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0
            else:
                features['spectral_rolloff'] = 0
            
            # Spectral Spread
            if features['spectral_centroid'] > 0:
                centroid = features['spectral_centroid']
                spread = np.sum(((freqs - centroid) ** 2) * fft_spectrum) / np.sum(fft_spectrum)
                features['spectral_spread'] = np.sqrt(spread)
            else:
                features['spectral_spread'] = 0
            
            # Spectral Skewness
            if features['spectral_centroid'] > 0 and features['spectral_bandwidth'] > 0:
                centroid = features['spectral_centroid']
                bandwidth = features['spectral_bandwidth']
                skewness = np.sum(((freqs - centroid) ** 3) * fft_spectrum) / (
                    np.sum(fft_spectrum) * (bandwidth ** 3)
                )
                features['spectral_skewness'] = skewness
            else:
                features['spectral_skewness'] = 0
            
            # Spectral Kurtosis
            if features['spectral_centroid'] > 0 and features['spectral_bandwidth'] > 0:
                centroid = features['spectral_centroid']
                bandwidth = features['spectral_bandwidth']
                kurt = np.sum(((freqs - centroid) ** 4) * fft_spectrum) / (
                    np.sum(fft_spectrum) * (bandwidth ** 4)
                ) - 3
                features['spectral_kurtosis'] = kurt
            else:
                features['spectral_kurtosis'] = 0
        
        # === Đặc trưng thời gian ===
        if data is not None and sr is not None:
            features['rms_energy'] = np.sqrt(np.mean(data ** 2))
            zero_crossings = np.where(np.diff(np.sign(data)))[0]
            features['zero_crossing_rate'] = len(zero_crossings) / len(data)
            features['peak_to_peak'] = np.max(data) - np.min(data)
            features['energy'] = np.sum(data ** 2)
        
        return features

    @staticmethod
    def cut_and_resample_fft(freqs, fft_spectrum, min_freq, max_freq, num_points=512):
        """
        Cắt và resample FFT về số điểm cố định
        
        Parameters:
        - freqs: mảng tần số gốc
        - fft_spectrum: mảng biên độ FFT
        - min_freq: tần số bắt đầu cắt
        - max_freq: tần số kết thúc cắt
        - num_points: số điểm mong muốn (mặc định 512)
        
        Returns:
        - new_freqs: mảng tần số mới (num_points điểm)
        - resampled_fft: mảng biên độ đã resample
        """
        from scipy.interpolate import interp1d
        
        # Lấy đoạn tần số cần cắt
        mask = (freqs >= min_freq) & (freqs <= max_freq)
        freq_cut = freqs[mask]
        fft_cut = fft_spectrum[mask]
        
        if len(freq_cut) < 3:
            return None, None
        
        # Tạo tần số mới (num_points điểm đều từ min đến max)
        new_freqs = np.linspace(min_freq, max_freq, num_points)
        
        # Nội suy để lấy giá trị tại num_points điểm
        interp_func = interp1d(freq_cut, fft_cut, kind='linear', 
                               bounds_error=False, fill_value=0)
        resampled_fft = interp_func(new_freqs)
        
        return new_freqs, resampled_fft

    # ===== HÀM LỌC TẦN SỐ VÀ IFFT =====
    @staticmethod
    def apply_filter_and_inverse_fft(data, sr, min_freq, max_freq):
        """
        Cắt tần số (lọc) và biến đổi ngược FFT để tạo lại âm thanh
        
        Parameters:
        - data: tín hiệu gốc
        - sr: sample rate
        - min_freq: tần số thấp nhất giữ lại
        - max_freq: tần số cao nhất giữ lại
        
        Returns:
        - filtered_data: tín hiệu đã lọc (chỉ giữ tần số trong khoảng min_freq-max_freq)
        """
        # FFT
        fft_data = np.fft.fft(data)
        freqs = np.fft.fftfreq(len(data), d=1/sr)
        
        # Tạo mask: chỉ giữ các tần số trong khoảng
        mask = (np.abs(freqs) >= min_freq) & (np.abs(freqs) <= max_freq)
        
        # Áp dụng mask (cắt bỏ tần số ngoài khoảng)
        fft_filtered = fft_data * mask
        
        # IFFT (biến đổi ngược về miền thời gian)
        filtered_data = np.fft.ifft(fft_filtered).real
        
        # Chuẩn hóa về [-1, 1]
        if np.max(np.abs(filtered_data)) > 0:
            filtered_data = filtered_data / np.max(np.abs(filtered_data))
        
        return filtered_data