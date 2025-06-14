import numpy as np
import sounddevice as sd
from scipy import signal
from rtlsdr import RtlSdr
import wave

# Parameters
center_freq = 95.7e6  # Target FM station in Hz
sample_rate = 1.024e6  # SDR sample rate
audio_rate = 48000  # Output audio sample rate
duration = 10  # seconds
gain = 42  # SDR gain

# Setup SDR
sdr = RtlSdr()
sdr.sample_rate = sample_rate
sdr.center_freq = center_freq
sdr.gain = gain

# Capture samples
num_samples = int(sample_rate * duration)
samples = sdr.read_samples(num_samples)
sdr.close()

# FM Demodulation
x = samples[1:] * np.conj(samples[:-1])
fm_demod = np.angle(x)

# Lowpass filter and decimate
cutoff = 16e3  # Hz
decim_factor = int(sample_rate // audio_rate)
b = signal.firwin(101, cutoff/(0.5*sample_rate))
audio = signal.lfilter(b, 1.0, fm_demod)[::decim_factor]

# Normalize and convert to int16
audio = audio / np.max(np.abs(audio))
audio_int16 = np.int16(audio * 32767)

# Save to WAV
with wave.open("radio_recording.wav", "w") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(audio_rate)
    f.writeframes(audio_int16.tobytes())

# Playback (optional)
# sd.play(audio, audio_rate, blocking=True)
