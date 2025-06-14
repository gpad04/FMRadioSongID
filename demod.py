import numpy as np
from scipy import signal
from rtlsdr import RtlSdr
import wave
import os

def record_fm_to_wav(center_freq=103.3e6, duration=10, output_file="song.wav", 
                     sample_rate=1.024e6, audio_rate=48000, gain=42):
    """
    Record FM radio to WAV file using RTL-SDR
    
    Args:
        center_freq (float): Target FM station frequency in Hz (default: 95.7 MHz)
        duration (int): Recording duration in seconds (default: 10)
        output_file (str): Output WAV filename (default: "song.wav")
        sample_rate (float): SDR sample rate (default: 1.024 MHz)
        audio_rate (int): Output audio sample rate (default: 48000 Hz)
        gain (int): SDR gain (default: 42)
    
    Returns:
        str: Path to the created WAV file
    
    Raises:
        Exception: If SDR initialization or recording fails
    """
    
    # Setup SDR
    if os.path.exists(output_file):
        os.remove(output_file)

    sdr = RtlSdr()
    try:
        sdr.sample_rate = sample_rate
        sdr.center_freq = center_freq
        sdr.gain = gain

        # Capture samples
        num_samples = int(sample_rate * duration)
        samples = sdr.read_samples(num_samples)
        
    finally:
        sdr.close()

    # FM Demodulation / Phase Differential
    x = samples[1:] * np.conj(samples[:-1])
    fm_demod = np.angle(x)

    # Lowpass filter and downsample
    cutoff = 16e3  # Hz
    decim_factor = int(sample_rate // audio_rate)
    b = signal.firwin(101, cutoff/(0.5*sample_rate))
    audio = signal.lfilter(b, 1.0, fm_demod)[::decim_factor]

    # Normalize and convert to int16
    audio = audio / np.max(np.abs(audio))
    audio_int16 = np.int16(audio * 32767)

    # Save to WAV
    with wave.open(output_file, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(audio_rate)
        f.writeframes(audio_int16.tobytes())

    return output_file

