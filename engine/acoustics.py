import math

class Vector3D:
    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float, y: float, z: float):
        self.x, self.y, self.z = x, y, z

    def dist(self, other: 'Vector3D') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)


class RoomAcousticsEngine:
    """
    Image-source ray tracer and acoustic spatializer.
    Optimized for bare-metal Python using sparse tapped-delay reflection events.
    """

    def __init__(self, room_dim: Vector3D, wall_absorption: float = 0.20, max_reflection_order: int = 2):
        self.L = room_dim
        self.refl_coeff = math.sqrt(1.0 - wall_absorption)
        self.order = max_reflection_order
        self.speed_of_sound = 343.0  # m/s

    def compute_impulse_response(self, src: Vector3D, mic: Vector3D, sample_rate: int = 44100) -> list[tuple[int, float]]:
        """
        Computes sparse acoustic ray arrivals.
        Returns a list of (sample_delay, gain_amplitude) reflection pairs.
        """
        sparse_ir = []

        for nx in range(-self.order, self.order + 1):
            for ny in range(-self.order, self.order + 1):
                for nz in range(-self.order, self.order + 1):
                    # Image source spatial positioning
                    ix = (2 * nx * self.L.x - src.x) if (nx % 2 != 0) else (2 * nx * self.L.x + src.x)
                    iy = (2 * ny * self.L.y - src.y) if (ny % 2 != 0) else (2 * ny * self.L.y + src.y)
                    iz = (2 * nz * self.L.z - src.z) if (nz % 2 != 0) else (2 * nz * self.L.z + src.z)

                    img_pos = Vector3D(ix, iy, iz)
                    d = mic.dist(img_pos)
                    if d < 1e-4:
                        continue

                    delay_sec = d / self.speed_of_sound
                    sample_idx = int(delay_sec * sample_rate)

                    # Spherical attenuation + wall boundary losses
                    reflections = abs(nx) + abs(ny) + abs(nz)
                    amplitude = (self.refl_coeff ** reflections) / (4.0 * math.pi * d)

                    sparse_ir.append((sample_idx, amplitude))

        return sparse_ir

    @staticmethod
    def convolve(signal: list[float], sparse_ir: list[tuple[int, float]], wet_dry: float = 0.35) -> list[float]:
        """
        Applies tapped-delay discrete convolution over non-zero reflection points.
        Complexity runs in O(N * K) where K is the ray count (~125), finishing in under 1 second.
        """
        sig_len = len(signal)
        wet = [0.0] * sig_len

        # Accumulate ray paths
        for delay, gain in sparse_ir:
            if gain < 1e-6 or delay >= sig_len:
                continue
            for i in range(sig_len - delay):
                wet[i + delay] += signal[i] * gain

        # Wet mix gain normalization
        max_val = max(max(abs(w) for w in wet), 1e-6)
        dry_gain = 1.0 - wet_dry
        wet_gain = wet_dry / max_val

        return [dry_gain * signal[n] + wet_gain * wet[n] for n in range(sig_len)]