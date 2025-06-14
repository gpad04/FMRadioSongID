# streamer.py
import asyncio
import numpy as np
import wave
import time
import os
from scipy import signal
from rtlsdr.rtlsdraio import RtlSdrAio
from acr_identify import identify_song

class LiveFMStreamer:
    def __init__(self, center_freq, output_dir=".", chunk_seconds=10):
        self.freq = center_freq
        self.output_dir = output_dir
        self.chunk_seconds = chunk_seconds
        self.running = False
        self.current_song_info = None
        self.audio_rate = 48000
        self.sample_rate = 1.024e6

    async def run(self):
        self.running = True
        sdr = RtlSdrAio()
        await sdr.set_sample_rate(self.sample_rate)
        await sdr.set_center_freq(self.freq)
        await sdr.set_gain(42)

        cutoff = 16e3
        b = signal.firwin(101, cutoff / (0.5 * self.sample_rate))
        decim_factor = int(self.sample_rate // self.audio_rate)

        audio_buffer = []
        last_save_time = time.time()

        try:
            async for samples in sdr.stream():
                x = samples[1:] * np.conj(samples[:-1])
                fm_demod = np.angle(x)
                audio = signal.lfilter(b, 1.0, fm_demod)[::decim_factor]
                audio_buffer.append(audio)

                if time.time() - last_save_time >= self.chunk_seconds:
                    filename = os.path.join(self.output_dir, f"live_{int(time.time())}.wav")
                    self._save_audio(audio_buffer, filename)
                    self.current_song_info = identify_song(filename)
                    print(f"🎶 Now playing: {self.current_song_info}")
                    audio_buffer = []
                    last_save_time = time.time()

                if not self.running:
                    break
        finally:
            await sdr.stop()
            sdr.close()

    def _save_audio(self, buffer, filepath):
        audio = np.concatenate(buffer)
        audio = audio / (np.max(np.abs(audio)) + 1e-6)
        audio_int16 = np.int16(audio * 32767)
        with wave.open(filepath, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.audio_rate)
            wf.writeframes(audio_int16.tobytes())

    def stop(self):
        self.running = False