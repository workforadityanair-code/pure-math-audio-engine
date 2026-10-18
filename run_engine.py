#!/usr/bin/env python3
"""
THE CYBERPUNK SYNTHWAVE ENGINE
Bare-Metal Math, Neural Arpeggios, Tape Saturation & ASCII Spectral Visualizer
"""

import math
import random
import time
from engine.wav_codec import WavCodec
from engine.dsp import SpectralEngine
from engine.synth import ADSR, BiquadFilter, Oscillator
from engine.neural import BareMetalNeuralCounterpoint
from engine.acoustics import Vector3D, RoomAcousticsEngine


def midi_to_freq(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def soft_clip_saturation(samples: list[float], drive: float = 1.8) -> list[float]:
    """Analog tape saturation using hyperbolic tangent (tanh) soft clipping."""
    return [math.tanh(s * drive) for s in samples]


def print_ascii_spectrogram(spectrum: list[float], bins: int = 36, max_height: int = 10):
    """Draws a vertical ASCII spectrum analyzer bar graph in the terminal."""
    print("\n" + "═" * 65)
    print(" ⚡ REAL-TIME RADIX-2 FFT SPECTRUM ANALYZER (LOG-DISTRIBUTED BINS)")
    print("═" * 65)

    # Sub-sample bins logarithmically to mimic visual graphic EQs
    display_bars = []
    step = len(spectrum) // (bins * 2)
    for b in range(bins):
        chunk = spectrum[b * step : (b + 1) * step + 1]
        val = max(chunk) if chunk else 0.0
        display_bars.append(min(max_height, int(val * 24.0)))

    for h in range(max_height, 0, -1):
        line = "  │ "
        for bar in display_bars:
            if bar >= h:
                line += "█ "
            elif bar == h - 1:
                line += "▄ "
            else:
                line += "  "
        print(line)

    print("  └" + "──" * bins)
    print("    20Hz       100Hz        500Hz        2kHz        8kHz     20kHz\n")


def generate_kick_transient(duration: float, sr: int = 44100) -> list[float]:
    """Generates an analog 808-style sine kick with fast exponential pitch drop."""
    total_samples = int(duration * sr)
    kick = [0.0] * total_samples
    phase = 0.0
    for i in range(total_samples):
        t = i / sr
        # Frequency sweeps from 160Hz down to 45Hz
        inst_freq = 45.0 + (160.0 - 45.0) * math.exp(-t * 32.0)
        phase += 2.0 * math.pi * inst_freq / sr
        amp = math.exp(-t * 7.0)
        kick[i] = math.sin(phase) * amp
    return kick


def main():
    random.seed(1337)
    sample_rate = 44100

    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║       ⚡ PURE-MATH CYBERPUNK GENERATIVE NEURAL SYNTHESIZER ⚡         ║
    ║   [Zero Frameworks • Bare-Metal Math • Procedural Counterpoint]      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)

    # 1. Train Neural Counterpoint on D Dorian (Dark Cyberpunk Vibe)
    print("» [1/5] Training Neural Counterpoint on D-Dorian scale...")
    # D3, E3, F3, G3, A3, B3, C4, D4
    dorian_midi = [50, 52, 53, 55, 57, 59, 60, 62]
    net = BareMetalNeuralCounterpoint(input_dim=8, hidden_dim=24, output_dim=8)

    # Train to produce 5ths, 7ths, and octaves for aggressive modal tension
    for _ in range(160):
        for i in range(8):
            one_hot = [1.0 if j == i else 0.0 for j in range(8)]
            net.train_step(one_hot, target_idx=(i + 4) % 8, lr=0.12)

    # 2. Composition Architecture: Dark Bassline + 16th Arp Lead
    print("» [2/5] Synthesizing Cyberpunk Bassline & Multi-Voice Neural Arps...")
    bass_progression = [0, 0, 2, 2, 4, 3, 0, 0]  # D -> F -> A -> G -> D
    bpm = 118
    beat_dur = 60.0 / bpm
    step_16th = beat_dur / 4.0

    lead_adsr = ADSR(attack_sec=0.015, decay_sec=0.06, sustain_level=0.3, release_sec=0.05, sample_rate=sample_rate)
    lead_env = lead_adsr.evaluate(step_16th)

    bass_adsr = ADSR(attack_sec=0.03, decay_sec=0.2, sustain_level=0.7, release_sec=0.1, sample_rate=sample_rate)
    bass_env = bass_adsr.evaluate(beat_dur)

    master_track = []

    # 8-bar progression loop
    for root_idx in bass_progression:
        root_midi = dorian_midi[root_idx]
        f_bass = midi_to_freq(root_midi)

        # A. FM Bass for the full beat duration
        raw_bass = Oscillator.generate_fm(
            carrier_f=f_bass,
            mod_f=f_bass * 1.0,
            mod_idx=2.8,
            duration=beat_dur,
            sr=sample_rate
        )

        # 808 transient punch
        kick = generate_kick_transient(duration=beat_dur, sr=sample_rate)

        min_bass_len = min(len(raw_bass), len(bass_env), len(kick))
        bass_chunk = [
            (raw_bass[i] * bass_env[i] * 0.6) + (kick[i] * 0.8)
            for i in range(min_bass_len)
        ]

        # B. 16th-Note Neural Arpeggiator
        arp_chunk = []
        for step in range(4):
            one_hot = [1.0 if j == ((root_idx + step) % 8) else 0.0 for j in range(8)]
            _, probs = net.forward(one_hot)
            lead_idx = max(range(8), key=lambda k: probs[k])
            f_lead = midi_to_freq(dorian_midi[lead_idx] + 24)

            voice_1 = Oscillator.generate_fm(f_lead, f_lead * 2.0, 0.8, step_16th, sample_rate)
            voice_2 = Oscillator.generate_sine(f_lead * 1.006, step_16th, sample_rate)

            step_len = min(len(voice_1), len(voice_2), len(lead_env))
            for i in range(step_len):
                arp_chunk.append((0.5 * voice_1[i] + 0.5 * voice_2[i]) * lead_env[i] * 0.45)

        # Mix both tracks safely using common bounded length
        mix_len = min(len(bass_chunk), len(arp_chunk))
        for i in range(mix_len):
            master_track.append(bass_chunk[i] + arp_chunk[i])

    # 3. Dynamic Filter & Warm Tape Saturation
    print("» [3/5] Applying Resonant Lowpass Filter + Analog Tape Saturation...")
    biquad = BiquadFilter(ftype='lowpass', cutoff_hz=3400.0, q=1.8, sample_rate=sample_rate)
    filtered = biquad.process(master_track)
    saturated = soft_clip_saturation(filtered, drive=1.5)

    # 4. Warehouse Reverb via Ray-Tracing
    print("» [4/5] Tracing 3D Warehouse Acoustics (12m x 10m x 4.5m space)...")
    warehouse = RoomAcousticsEngine(
        room_dim=Vector3D(12.0, 10.0, 4.5),
        wall_absorption=0.32,
        max_reflection_order=2
    )
    ir = warehouse.compute_impulse_response(
        src=Vector3D(2.5, 3.0, 1.8),
        mic=Vector3D(9.0, 7.5, 1.6),
        sample_rate=sample_rate
    )
    spatialized = warehouse.convolve(saturated, ir, wet_dry=0.28)

    # 5. Spectral Visualization & Export
    print("» [5/5] Running FFT & Rendering ASCII Display...")
    # Analyze a steady-state slice of audio (around the 2nd second)
    fft_start = sample_rate * 2
    fft_window = spatialized[fft_start : fft_start + 2048]
    spectrum = SpectralEngine.get_magnitude_spectrum(fft_window)
    print_ascii_spectrogram(spectrum, bins=28, max_height=8)

    out_file = "cyberpunk_synth_engine.wav"
    WavCodec.write_pcm16_mono(out_file, spatialized, sample_rate)
    print(f"✔ RENDER COMPLETE: '{out_file}' generated successfully.")


if __name__ == '__main__':
    main()