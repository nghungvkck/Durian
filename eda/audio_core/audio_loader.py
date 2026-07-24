"""
Hàm load audio file - Hỗ trợ WAV, MP3, M4A, FLAC, OGG
"""

import numpy as np
import warnings

warnings.filterwarnings('ignore', category=UserWarning)

# Kiểm tra thư viện có sẵn
HAS_LIBROSA = False
HAS_SOUNDFILE = False
HAS_SCIPY = False

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    pass

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    pass

try:
    from scipy.io import wavfile
    HAS_SCIPY = True
except ImportError:
    pass


def load_audio(filepath):
    """
    Load audio file - hỗ trợ nhiều định dạng
    
    Returns:
        data: numpy array (float32)
        sr: sample rate
        method: string ('librosa', 'soundfile', 'scipy', 'ffmpeg')
    """
    
    # === Cách 1: Dùng librosa ===
    if HAS_LIBROSA:
        try:
            data, sr = librosa.load(filepath, sr=None, mono=True, dtype=np.float32)
            return data, sr, 'librosa'
        except:
            pass
    
    # === Cách 2: Dùng soundfile ===
    if HAS_SOUNDFILE:
        try:
            data, sr = sf.read(filepath, dtype='float32')
            if len(data.shape) > 1:
                data = data[:, 0]
            return data, sr, 'soundfile'
        except:
            pass
    
    # === Cách 3: Dùng scipy ===
    if HAS_SCIPY:
        try:
            sr, data = wavfile.read(filepath)
            if len(data.shape) > 1:
                data = data[:, 0]
            data = data.astype(np.float32) / 32768.0
            return data, sr, 'scipy'
        except:
            pass
    
    return None, None, None


def load_audio_simple(filepath):
    """
    Load audio file - trả về data và sr (đơn giản)
    """
    data, sr, _ = load_audio(filepath)
    return data, sr