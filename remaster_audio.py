#!/usr/bin/env python3
"""
Bare-Metal External Audio Ingestion & Spatial Remastering Engine
"""

import sys
import os
from engine.wav_codec import WavCodec
from engine.dsp import SpectralEngine
from engine.acoustics import Vector3D, RoomAcousticsEngine
from run_engine import soft_clip_saturation, print_ascii_spectrogram


def process_external_track(input_path: str, output_path: str = "remastered_spatial.wav"):
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    print(f"» Reading binary PCM stream from '{input_path}'...")
    sr, samples = WavCodec.read_pcm16_mono(input_path)
    print(f"  Sample Rate: {sr} Hz | Total Samples: {len(samples)} ({len(samples)/sr:.2f}s)")

    # 1. Pre-Processing Spectrum
    print("» Running FFT on input audio...")
    fft_frame = samples[min(sr, len(samples)//2) : min(sr, len(samples)//2) + 2048]
    if len(fft_frame) == 2048:
        spectrum = SpectralEngine.get_magnitude_spectrum(fft_frame)
        print("  Original Frequency Spectrum:")
        print_ascii_spectrogram(spectrum, bins=24, max_height=6)

    # 2. Virtual Chamber Acoustics
    print("» Placing audio inside a 3D Concert Hall acoustic model (18m x 14m x 6m)...")
    hall = RoomAcousticsEngine(
        room_dim=Vector3D(18.0, 14.0, 6.0),
        wall_absorption=0.22,
        max_reflection_order=2
    )
    # Source at front-left stage, listener in mid-hall
    ir = hall.compute_impulse_response(
        src=Vector3D(3.0, 4.0, 1.5),
        mic=Vector3D(12.0, 9.0, 1.6),
        sample_rate=sr
    )
    spatialized = hall.convolve(samples, ir, wet_dry=0.30)

    # 3. Analog Warmth
    print("» Applying hyperbolic tangent tape saturation...")
    mastered = soft_clip_saturation(spatialized, drive=1.2)

    # 4. Binary serialization
    print(f"» Writing remastered stream to '{output_path}'...")
    WavCodec.write_pcm16_mono(output_path, mastered, sample_rate=sr)
    print("✔ Remaster complete!")


if __name__ == '__main__':
    # You can pass any wav file directly, or test it on our generated track
    target = sys.argv[1] if len(sys.argv) > 1 else "cyberpunk_synth_engine.wav"
    process_external_track(target)