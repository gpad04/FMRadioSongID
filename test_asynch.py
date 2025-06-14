import asyncio
from rtlsdr.rtlsdraio import RtlSdrAio

async def main():
    print("Creating SDR...")
    sdr = RtlSdrAio()
    sdr.sample_rate = 1.024e6
    sdr.center_freq = 106.1e6
    sdr.gain = 42

    print("Reading 1024*32 samples...")
    try:
        samples = sdr.read_samples(1024*32)
        print("Got", len(samples), "samples")
    except Exception as e:
        print("Error reading samples:", e)

    sdr.close()

asyncio.run(main())