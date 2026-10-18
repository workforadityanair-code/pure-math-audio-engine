import math
import unittest
from engine.synth import ADSR, BiquadFilter

class TestSynthPrimitives(unittest.TestCase):
    def test_adsr_boundaries(self):
        adsr = ADSR(attack_sec=0.01, decay_sec=0.02, sustain_level=0.5, release_sec=0.02, sample_rate=1000)
        env = adsr.evaluate(0.1)
        self.assertGreater(len(env), 0)
        self.assertAlmostEqual(env[0], 0.0, delta=0.05)
        self.assertTrue(all(0.0 <= x <= 1.05 for x in env))

    def test_biquad_stability(self):
        # Ensure filter does not blow up or output NaNs
        biquad = BiquadFilter(ftype='lowpass', cutoff_hz=1000.0, q=1.0, sample_rate=44100)
        impulse = [1.0] + [0.0] * 127
        response = biquad.process(impulse)
        self.assertTrue(all(not math.isnan(x) and abs(x) < 2.0 for x in response))

if __name__ == '__main__':
    unittest.main()