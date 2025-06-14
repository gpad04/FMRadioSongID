import os
import eventlet

from acr_identify import identify_song
eventlet.monkey_patch()
from flask import Flask, render_template
from flask import send_from_directory
from flask_socketio import SocketIO
import asyncio
import numpy as np
from scipy import signal
from rtlsdr.rtlsdraio import RtlSdr
from demod import record_fm_to_wav
import threading

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", 
                   logger=True, engineio_logger=True)

def rtl_sdr_audio_generator(center_freq=103.3e6, duration = 10, sample_rate=1.024e6, audio_rate=48000, chunk_size=1024):
    """
    Generator yielding float32 PCM chunks from RTL-SDR demodulated FM audio.
    """
    print("Initializing RTL-SDR...")
    sdr = RtlSdr()
    sdr.sample_rate = sample_rate
    sdr.center_freq = center_freq
    sdr.gain = 42

    print("Setting up filters...")
    cutoff = 16e3  # Hz
    b = signal.firwin(101, cutoff / (0.5 * sample_rate))
    decim_factor = int(sample_rate // audio_rate)
    leftover = np.array([], dtype=np.float32)

    try:
        print("Starting sample loop...")
        while True:
            samples = sdr.read_samples(1024 * 32)

            # FM demodulation
            x = samples[1:] * np.conj(samples[:-1])
            fm_demod = np.angle(x)

            # Low-pass filter
            filtered = signal.lfilter(b, 1.0, fm_demod)

            # Decimate to audio rate
            audio = filtered[::decim_factor]
            audio = np.concatenate((leftover, audio))

            while len(audio) >= chunk_size:
                chunk = audio[:chunk_size]
                audio = audio[chunk_size:]

                # Normalize
                if np.max(np.abs(chunk)) > 0:
                    chunk = chunk / np.max(np.abs(chunk))

                yield chunk.astype(np.float32)

            leftover = audio
    finally:
        print("Closing SDR...")
        sdr.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/song.wav')
def serve_song():
    return send_from_directory('.', 'song.wav')

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('start_stream')
def handle_start_stream(data):
    print("Starting audio stream...")

    center_freq = data.get('center_freq', 106.1e6) * 1e6
    
    def run_audio_emit():
        def send_chunks():
            try:
                chunk_count = 0
                for chunk in rtl_sdr_audio_generator(center_freq=center_freq):
                    socketio.emit('audio_chunk', chunk.tobytes())
                    chunk_count += 1
                    if chunk_count % 100 == 0:
                        print(f"Sent {chunk_count} audio chunks")
                    eventlet.sleep(0.01)
            except Exception as e:
                print("Streaming error:", e)

        send_chunks()
    
    # Use threading instead of SocketIO background task for better async handling
    thread = threading.Thread(target=run_audio_emit)
    thread.daemon = True
    thread.start()

@socketio.on('start_identify')
def handle_start_identify(data):
    center_freq = data.get('center_freq', 106.1e6) * 1e6
    audio_filename = "song.wav"  # Always overwrite

    try:
        record_fm_to_wav(center_freq=center_freq, duration=10, output_file=audio_filename)
        result = identify_song(audio_filename)
    except Exception as e:
        result = {"title": "Error", "artist": str(e)}

    socketio.emit('identify_result', {
        "title": result.get("title", "Unknown"),
        "artist": result.get("artist", "Unknown"),
        "file": audio_filename
    })


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)