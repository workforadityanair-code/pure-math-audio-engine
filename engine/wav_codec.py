import struct

class WavCodec:
    """Encodes and decodes canonical 16-bit signed PCM RIFF WAVE byte streams."""

    @staticmethod
    def write_pcm16_mono(filepath: str, samples: list[float], sample_rate: int = 44100) -> None:
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

    @staticmethod
    def read_pcm16_mono(filepath: str) -> tuple[int, list[float]]:
        """Scans arbitrary RIFF chunk hierarchies to accurately parse any PCM WAV."""
        with open(filepath, 'rb') as f:
            riff, file_size, wave = struct.unpack('<4sI4s', f.read(12))
            if riff != b'RIFF' or wave != b'WAVE':
                raise ValueError("Not a valid RIFF/WAVE container.")

            sample_rate = 44100
            channels = 1
            audio_format = 1
            bits_per_sample = 16
            pcm_data = b""

            # Scan through chunks until EOF
            while True:
                chunk_header = f.read(8)
                if len(chunk_header) < 8:
                    break
                chunk_id, chunk_sz = struct.unpack('<4sI', chunk_header)

                if chunk_id == b'fmt ':
                    fmt_data = f.read(chunk_sz)
                    audio_format, channels, sample_rate, _, _, bits_per_sample = struct.unpack('<HHIIHH', fmt_data[:16])
                elif chunk_id == b'data':
                    pcm_data = f.read(chunk_sz)
                    break  # Found audio data stream
                else:
                    # Skip metadata chunks (LIST, INFO, etc.)
                    f.seek(chunk_sz, 1)

            if audio_format != 1 or bits_per_sample != 16:
                raise ValueError("Only 16-bit uncompressed PCM is supported.")

            total_samples = len(pcm_data) // (2 * channels)
            raw_ints = struct.unpack(f'<{total_samples * channels}h', pcm_data[:total_samples * channels * 2])

            # Extract mono / first channel normalized to [-1.0, 1.0]
            samples = [raw_ints[i * channels] / 32767.0 for i in range(total_samples)]
            return sample_rate, samples