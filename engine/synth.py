import math

class ADSR:
    def __init__(self, attack_sec: float, decay_sec: float, sustain_level: float, release_sec: float, sample_rate: int = 44100):
        self.sr = sample_rate
        self.attack_samples = max(1, int(attack_sec * sample_rate))
        self.decay_samples = max(1, int(decay_sec * sample_rate))
        self.sustain_level = max(0.0, min(1.0, sustain_level))
        self.release_samples = max(1, int(release_sec * sample_rate))

    def evaluate(self, duration_sec: float) -> list[float]:
        total_samples = int(duration_sec * self.sr)
        env = [0.0] * total_samples
        sustain_samples = max(0, total_samples - (self.attack_samples + self.decay_samples + self.release_samples))

        i = 0
        for t in range(self.attack_samples):
            if i >= total_samples: break
            env[i] = t / float(self.attack_samples)
            i += 1

        for t in range(self.decay_samples):
            if i >= total_samples: break
            progress = t / float(self.decay_samples)
            env[i] = self.sustain_level + (1.0 - self.sustain_level) * math.exp(-3.0 * progress)
            i += 1

        for _ in range(sustain_samples):
            if i >= total_samples: break
            env[i] = self.sustain_level
            i += 1

        release_start = env[i - 1] if i > 0 else self.sustain_level
        for t in range(self.release_samples):
            if i >= total_samples: break
            progress = t / float(self.release_samples)
            env[i] = release_start * (1.0 - progress) * math.exp(-progress)
            i += 1

        return env


class BiquadFilter:
    """Direct Form II Transposed IIR Biquad Filter."""

    def __init__(self, ftype: str, cutoff_hz: float, q: float, sample_rate: int = 44100):
        self.sr = sample_rate
        self.d1 = 0.0
        self.d2 = 0.0

        omega = 2.0 * math.pi * cutoff_hz / self.sr
        alpha = math.sin(omega) / (2.0 * q)
        cos_w = math.cos(omega)

        if ftype == 'lowpass':
            b0 = (1.0 - cos_w) / 2.0
            b1 = 1.0 - cos_w
            b2 = (1.0 - cos_w) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cos_w
            a2 = 1.0 - alpha
        elif ftype == 'bandpass':
            b0 = alpha
            b1 = 0.0
            b2 = -alpha
            a0 = 1.0 + alpha
            a1 = -2.0 * cos_w
            a2 = 1.0 - alpha
        else:
            raise NotImplementedError(f"Filter type {ftype} not implemented.")

        self.b0 = b0 / a0
        self.b1 = b1 / a0
        self.b2 = b2 / a0
        self.a1 = a1 / a0
        self.a2 = a2 / a0

    def process(self, x: list[float]) -> list[float]:
        out = [0.0] * len(x)
        b0, b1, b2 = self.b0, self.b1, self.b2
        a1, a2 = self.a1, self.a2
        d1, d2 = self.d1, self.d2

        for i, sample in enumerate(x):
            y = b0 * sample + d1
            d1 = b1 * sample - a1 * y + d2
            d2 = b2 * sample - a2 * y
            out[i] = y

        self.d1, self.d2 = d1, d2
        return out


class Oscillator:
    @staticmethod
    def generate_sine(freq: float, duration: float, sr: int = 44100, phase: float = 0.0) -> list[float]:
        total_samples = int(duration * sr)
        step = 2.0 * math.pi * freq / sr
        return [math.sin(phase + i * step) for i in range(total_samples)]

    @staticmethod
    def generate_fm(carrier_f: float, mod_f: float, mod_idx: float, duration: float, sr: int = 44100) -> list[float]:
        total_samples = int(duration * sr)
        carrier_step = 2.0 * math.pi * carrier_f / sr
        mod_step = 2.0 * math.pi * mod_f / sr
        signal = [0.0] * total_samples
        for i in range(total_samples):
            modulator = mod_idx * math.sin(i * mod_step)
            signal[i] = math.sin(i * carrier_step + modulator)
        return signal

class Noise:
    """Linear Congruential Generator (LCG) for deterministic white noise."""
    def __init__(self, seed: int = 123456789):
        self.state = seed

    def next_sample(self) -> float:
        # Standard POSIX LCG constants
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        # Normalize to [-1.0, 1.0]
        return (self.state / 1073741823.5) - 1.0

    def generate(self, duration: float, sr: int = 44100) -> list[float]:
        total = int(duration * sr)
        return [self.next_sample() for _ in range(total)]