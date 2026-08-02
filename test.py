import numpy as np

# Create the signal: 300 Hz + 700 Hz
sr = 8000  # sampling rate
t = np.linspace(0, 1, sr, endpoint=False)  # 1 second of audio
g = np.sin(2 * np.pi * 300 * t) + np.sin(2 * np.pi * 700 * t)

# Apply Fourier Transform - this is doing the winding + COM for all frequencies at once
fft_result = np.fft.rfft(g)

# Get magnitudes (amplitude of contribution for each frequency)
magnitudes = np.abs(fft_result)

# Get the frequency values corresponding to each bin
freqs = np.fft.rfftfreq(len(g), d=1/sr)

# The peaks in magnitudes will be at 300 Hz and 700 Hz
# Everything else will be near zero