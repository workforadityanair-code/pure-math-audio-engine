#!/usr/bin/env python3
"""
Bare-Metal Real-Time Keyboard Synthesizer
Zero third-party libraries: uses standard `msvcrt` for key input
and standard `winsound` for asynchronous file playback.
"""

import math
import msvcrt
import os
import struct
import tempfile
import winsound
from engine.synth import ADSR, BiquadFilter, Oscillator


def midi_to_freq(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def write_pcm16_mono(filepath: str, samples: list[float], sample_rate: int = 44100):
    """Writes a short 16-bit PCM WAV to disk for winsound async playback."""
    num_samples = len(samples)
    byte_rate = sample_rate * 2
    block_align = 2
    subchunk2_size = num_samples * 2
    chunk_size = 36 + subchunk2_size

    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        chunk_size,
        b'WAVE',
        b'fmt ',
        16,
        1,
        1,
        sample_rate,
        byte_rate,
        block_align,
        16,
        b'data',
        subchunk2_size
    )

    with open(filepath, 'wb') as f:
        f.write(header)
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            quantized = int(clamped * 32767.0)
            f.write(struct.pack('<h', quantized))


class LiveSynthesizer:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.note_duration = 0.35
        self.adsr = ADSR(
            attack_sec=0.015,
            decay_sec=0.08,
            sustain_level=0.4,
            release_sec=0.12,
            sample_rate=self.sample_rate
        )
        self.env = self.adsr.evaluate(self.note_duration)
        self.filter = BiquadFilter(ftype='lowpass', cutoff_hz=3200.0, q=1.5, sample_rate=self.sample_rate)

        # Temporary directory to hold the cached wav snippets
        self.temp_dir = tempfile.mkdtemp(prefix="bare_metal_synth_")

        self.key_map = {
            b'a': 60,  # C4
            b'w': 61,  # C#4
            b's': 62,  # D4
            b'e': 63,  # D#4
            b'd': 64,  # E4
            b'f': 65,  # F4
            b't': 66,  # F#4
            b'g': 67,  # G4
            b'y': 68,  # G#4
            b'h': 69,  # A4
            b'u': 70,  # A#4
            b'j': 71,  # B4
            b'k': 72,  # C5
        }
        self.file_cache: dict[bytes, str] = {}
        self._precompute_audio()

    def _precompute_audio(self):
        print("» Pre-caching synthesizer waveforms...")
        for key, midi in self.key_map.items():
            freq = midi_to_freq(midi)

            fm_lead = Oscillator.generate_fm(
                carrier_f=freq,
                mod_f=freq * 2.0,
                mod_idx=1.4,
                duration=self.note_duration,
                sr=self.sample_rate
            )
            sub_sine = Oscillator.generate_sine(freq * 0.5, self.note_duration, sr=self.sample_rate)

            chunk = [
                (0.6 * fm_lead[i] + 0.4 * sub_sine[i]) * self.env[i]
                for i in range(len(self.env))
            ]

            filtered_chunk = self.filter.process(chunk)
            saturated_chunk = [math.tanh(s * 1.5) for s in filtered_chunk]

            file_path = os.path.join(self.temp_dir, f"note_{midi}.wav")
            write_pcm16_mono(file_path, saturated_chunk, self.sample_rate)
            self.file_cache[key] = file_path

    def play_key(self, key: bytes):
        if key in self.file_cache:
            # SND_FILENAME + SND_ASYNC works without errors
            winsound.PlaySound(
                self.file_cache[key],
                winsound.SND_FILENAME | winsound.SND_ASYNC
            )

    def cleanup(self):
        for path in self.file_cache.values():
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass


def main():
    synth = LiveSynthesizer()

    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                 ⚡ LIVE BARE-METAL KEYBOARD SYNTH ⚡             ║
    ║                                                                  ║
    ║   White Keys:  [ A ] [ S ] [ D ] [ F ] [ G ] [ H ] [ J ] [ K ]   ║
    ║   Notes:        C4    D4    E4    F4    G4    A4    B4    C5     ║
    ║                                                                  ║
    ║   Black Keys:     [ W ] [ E ]       [ T ] [ Y ] [ U ]            ║
    ║   Notes:           C#4   D#4         F#4   G#4   A#4             ║
    ║                                                                  ║
    ║   Press [ESC] or [Q] to exit.                                    ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    try:
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().lower()
                if key in (b'\x1b', b'q'):
                    print("\nExiting live synthesizer.")
                    break
                if key in synth.key_map:
                    synth.play_key(key)
    finally:
        synth.cleanup()


if __name__ == '__main__':
    main()