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
        """Phát hiện các đỉnh (peaks) trong tín hiệu"""
        abs_data = np.abs(data)
        min_dist_samples = int(min_distance * sr)
        peaks, properties = find_peaks(abs_data, height=threshold, distance=min_dist_samples)
        if len(peaks) == 0:
            return np.array([]), np.array([])
        return peaks, properties['peak_heights']
    
    @staticmethod
    def extract_segments(data, sr, peaks, pre_peak=0.05, duration=0.1):
        """Trích xuất các đoạn (segments) xung quanh mỗi peak"""
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
    def compute_fft(segments, sr, max_freq=None):
        """Tính FFT trung bình từ các segments"""
        if not segments:
            return None, None, None
        
        ffts = []
        freq_axes = []
        
        for seg in segments:
            data = seg['data']
            N = len(data)
            window = np.hanning(N)
            fft_amp = np.abs(np.fft.fft(data * window))[:N//2]
            if np.max(fft_amp) > 0:
                fft_amp = fft_amp / np.max(fft_amp)
            ffts.append(fft_amp)
            freq_axes.append(np.fft.fftfreq(N, d=1/sr)[:N//2])
        
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
        
        avg_fft = np.mean(resampled, axis=0)
        peaks_fft, _ = find_peaks(avg_fft, height=0.1, distance=5)
        
        if max_freq:
            mask = common_freq <= max_freq
            return common_freq[mask], avg_fft[mask], [p for p in peaks_fft if p < len(mask) and mask[p]]
        
        return common_freq, avg_fft, peaks_fft

    # ===== PHẦN THÊM MỚI: TRÍCH XUẤT ĐẶC TRƯNG =====
    
    @staticmethod
    def extract_features_from_segments(segments, sr, freqs=None, avg_fft=None):
        """
        Trích xuất đặc trưng từ các segments đã chọn
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
        """
        features = {}
        
        # === Đặc trưng tần số ===
        if len(freqs) > 0 and len(fft_spectrum) > 0:
            peak_idx = np.argmax(fft_spectrum)
            features['peak_freq'] = freqs[peak_idx]
            features['peak_mag'] = fft_spectrum[peak_idx]
            
            if np.sum(fft_spectrum) > 0:
                features['spectral_centroid'] = np.sum(freqs * fft_spectrum) / np.sum(fft_spectrum)
            else:
                features['spectral_centroid'] = 0
            
            if features['spectral_centroid'] > 0:
                centroid = features['spectral_centroid']
                variance = np.sum(((freqs - centroid) ** 2) * fft_spectrum) / np.sum(fft_spectrum)
                features['spectral_bandwidth'] = np.sqrt(variance)
            else:
                features['spectral_bandwidth'] = 0
            
            cumsum = np.cumsum(fft_spectrum)
            total = cumsum[-1]
            if total > 0:
                rolloff_idx = np.where(cumsum >= 0.85 * total)[0]
                features['spectral_rolloff'] = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0
            else:
                features['spectral_rolloff'] = 0
            
            if features['spectral_centroid'] > 0:
                centroid = features['spectral_centroid']
                spread = np.sum(((freqs - centroid) ** 2) * fft_spectrum) / np.sum(fft_spectrum)
                features['spectral_spread'] = np.sqrt(spread)
            else:
                features['spectral_spread'] = 0
            
            if features['spectral_centroid'] > 0 and features['spectral_bandwidth'] > 0:
                centroid = features['spectral_centroid']
                bandwidth = features['spectral_bandwidth']
                skewness = np.sum(((freqs - centroid) ** 3) * fft_spectrum) / (
                    np.sum(fft_spectrum) * (bandwidth ** 3)
                )
                features['spectral_skewness'] = skewness
            else:
                features['spectral_skewness'] = 0
            
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