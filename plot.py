import wave
import numpy as np
import matplotlib.pyplot as plt

filename = "./esp32/src/20260708_103807_765178.wav"

with wave.open(filename, "rb") as wf:

    sampleCount = wf.getnframes()

    audio = np.frombuffer(
        wf.readframes(sampleCount),
        dtype=np.int16
    )

time = np.arange(sampleCount) / 16000

plt.figure(figsize=(12,4))
plt.plot(time, audio)

plt.title(filename)
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")

plt.grid(True)

plt.show()