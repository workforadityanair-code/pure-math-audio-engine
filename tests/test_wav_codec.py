import os
import unittest
from engine.wav_codec import WavCodec

class TestWavCodec(unittest.TestCase):
    def setUp(self):
        self.test_filename = "test_artifact.wav"

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_roundtrip_pcm16(self):
        sr = 44100
        # 100 samples of a synthetic pulse train
        original_samples = [(-1.0 + 2.0 * (i / 100.0)) for i in range(100)]
        WavCodec.write_pcm16_mono(self.test_filename, original_samples, sample_rate=sr)

        read_sr, recovered_samples = WavCodec.read_pcm16_mono(self.test_filename)
        self.assertEqual(sr, read_sr)
        self.assertEqual(len(original_samples), len(recovered_samples))

        # Check quantization error is within 16-bit noise floor (1 / 32767)
        for orig, rec in zip(original_samples, recovered_samples):
            self.assertAlmostEqual(orig, rec, delta=1.0 / 32767.0)

if __name__ == '__main__':
    unittest.main()