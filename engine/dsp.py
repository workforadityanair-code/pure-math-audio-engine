import cmath
import math

class SpectralEngine:
    """In-place Radix-2 Decimation-In-Time Cooley-Tukey FFT."""

    @staticmethod
    def _bit_reverse_indices(n: int) -> list[int]:
        rev = [0] * n
        bits = n.bit_length() - 1
        for i in range(n):
            r = 0
            for j in range(bits):
                if (i >> j) & 1:
                    r |= 1 << (bits - 1 - j)
            rev[i] = r
        return rev

    @staticmethod
    def fft(signal: list[complex]) -> list[complex]:
        n = len(signal)
        if n & (n - 1) != 0:
            next_pow2 = 1 << (n - 1).bit_length()
            signal = signal + [0j] * (next_pow2 - n)
            n = next_pow2

        rev = SpectralEngine._bit_reverse_indices(n)
        a = [signal[rev[i]] for i in range(n)]

        length = 2
        while length <= n:
            half = length // 2
            angle = -2.0 * math.pi / length
            w_step = cmath.rect(1.0, angle)

            for i in range(0, n, length):
                w = complex(1.0, 0.0)
                for j in range(half):
                    u = a[i + j]
                    v = a[i + j + half] * w
                    a[i + j] = u + v
                    a[i + j + half] = u - v
                    w *= w_step
            length <<= 1

        return a

    @staticmethod
    def get_magnitude_spectrum(signal: list[float]) -> list[float]:
        c_signal = [complex(x, 0.0) for x in signal]
        transformed = SpectralEngine.fft(c_signal)
        half_n = len(transformed) // 2
        return [abs(transformed[i]) / half_n for i in range(half_n)]