import math
import unittest
from engine.dsp import SpectralEngine

class TestSpectralEngine(unittest.TestCase):
    def test_fft_fundamental_detection(self):
        sr = 44100
        n_samples = 1024
        target_freq = 440.0  # A4

        # Generate pure sine test window
        sine_wave = [
            math.sin(2.0 * math.pi * target_freq * i / sr)
            for i in range(n_samples)
        ]

        spectrum = SpectralEngine.get_magnitude_spectrum(sine_wave)
        dominant_bin = max(range(len(spectrum)), key=lambda k: spectrum[k])
        detected_freq = dominant_bin * (sr / n_samples)

        # 44100 / 1024 gives ~43.06 Hz bin resolution; check proximity
        self.assertAlmostEqual(target_freq, detected_freq, delta=45.0)

if __name__ == '__main__':
    unittest.main()