import wave
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from scipy.signal import find_peaks

filename = "./esp32/src/dataset/Máy gõ/20260717_190113.wav"

# Đọc file âm thanh
with wave.open(filename, "rb") as wf:
    sampleCount = wf.getnframes()
    sampleRate = wf.getframerate()
    audio = np.frombuffer(wf.readframes(sampleCount), dtype=np.int16)

print(f"✅ Sample rate: {sampleRate} Hz")
print(f"✅ Duration: {len(audio)/sampleRate:.2f}s")

# Tạo figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# ---- Spectrogram ----
ax1.specgram(audio,
             Fs=sampleRate,
             NFFT=1024,
             noverlap=512,
             cmap='jet')

ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Frequency (Hz)")
ax1.set_title("📊 Spectrogram - Khoanh vùng để xem FFT")
ax1.set_ylim(0, 8000)
ax1.grid(True, alpha=0.3)

# ---- FFT ----
ax2.set_xlabel("Frequency (Hz)")
ax2.set_ylabel("Magnitude")
ax2.set_title("📈 Frequency Spectrum")
ax2.set_xlim(0, 8000)
ax2.grid(True, alpha=0.3)


def on_select(eclick, erelease):
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata

    if None in [x1, x2, y1, y2]:
        return

    t_start = min(x1, x2)
    t_end = max(x1, x2)
    f_start = min(y1, y2)
    f_end = max(y1, y2)

    idx_start = max(0, int(t_start * sampleRate))
    idx_end = min(len(audio), int(t_end * sampleRate))

    if idx_end - idx_start < 100:
        print("⚠️ Chọn vùng dài hơn (ít nhất 100 mẫu).")
        return

    segment = audio[idx_start:idx_end]
    N = len(segment)

    fft = np.fft.rfft(segment)
    freq = np.fft.rfftfreq(N, d=1 / sampleRate)
    magnitude = np.abs(fft)

    ax2.clear()

    # FFT gốc
    ax2.plot(freq, magnitude, color="black", linewidth=1, alpha=0.8, label="FFT")

    # Tìm đỉnh với threshold adaptive
    threshold = np.percentile(magnitude, 85)
    min_distance = max(10, int(sampleRate * 0.003))
    
    peaks, properties = find_peaks(
        magnitude,
        height=threshold,
        distance=min_distance
    )

    if len(peaks) == 0:
        print("⚠️ Không tìm thấy đỉnh nào!")
        ax2.set_xlim(0, 8000)
        ax2.grid(True, linestyle="--", alpha=0.4)
        fig.canvas.draw_idle()
        return

    peak_freq = freq[peaks]
    peak_mag = magnitude[peaks]

    # Chỉ giữ 10 đỉnh lớn nhất
    if len(peak_mag) > 10:
        idx = np.argsort(peak_mag)[-10:]
        idx = idx[np.argsort(peak_freq[idx])]
        peak_freq = peak_freq[idx]
        peak_mag = peak_mag[idx]

    # Vẽ đỉnh
    ax2.plot(
        peak_freq,
        peak_mag,
        "-o",
        color="red",
        linewidth=2.5,
        markersize=8,
        markerfacecolor="red",
        markeredgecolor="white",
        markeredgewidth=1.5,
        label="Main Peaks"
    )

    # Đánh dấu vùng tần số đã chọn
    ax2.axvspan(f_start, f_end, color="gold", alpha=0.3, edgecolor='orange', linewidth=2)

    ax2.set_xlim(0, 8000)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude")
    ax2.set_title(f"FFT ({t_start:.2f}s - {t_end:.2f}s)")
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc='upper right')

    # Hiển thị bảng thông số
    if len(peak_freq) > 0:
        table_data = []
        for f, m in zip(peak_freq[:5], peak_mag[:5]):
            table_data.append([f"{f:.0f}", f"{m:.2f}"])
        
        table = ax2.table(cellText=table_data,
                          colLabels=['Frequency (Hz)', 'Magnitude'],
                          loc='upper left',
                          cellLoc='center',
                          colWidths=[0.15, 0.15])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)

    fig.canvas.draw_idle()

    if len(peak_mag) > 0:
        max_idx = np.argmax(peak_mag)
        print(f"✅ Peak lớn nhất: {peak_freq[max_idx]:.1f} Hz (magnitude: {peak_mag[max_idx]:.1f})")


# === KÍCH HOẠT RectangleSelector với thiết kế đẹp ===
selector = RectangleSelector(
    ax1,
    on_select,
    useblit=True,
    button=[1],
    minspanx=10,
    minspany=10,
    spancoords='pixels',
    interactive=True,
    props=dict(
        facecolor='cyan',
        edgecolor='white',
        alpha=0.3,
        linestyle='-',
        linewidth=3,
        fill=True
    )
)

# Thêm hướng dẫn sử dụng
ax1.text(0.02, 0.98, 
         "🖱️ Kéo thả chuột để chọn vùng\nNhấn Enter để xóa chọn",
         transform=ax1.transAxes,
         fontsize=10,
         verticalalignment='top',
         bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8))

plt.tight_layout()
plt.show()