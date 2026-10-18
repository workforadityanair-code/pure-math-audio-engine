# Pure-Math Generative Neural Synthesizer & Spatial Acoustic Engine

A bare-metal digital audio workstation, procedural music synthesizer, and physical acoustics simulator built completely from scratch in pure Python.

**Zero third-party audio or machine learning dependencies**—constructed strictly using standard library mathematical primitives (`math`, `struct`, `cmath`, `random`).

---

## Architecture Overview
[ Markov / Neural Counterpoint Engine ]
│ (Note events & modal intervals)
▼
[ Multi-Voice Polyphonic Synthesizer ]
├── Sine / Saw / Square / FM Wave Generators
├── Exponential ADSR Envelope Engines
└── Direct Form II Transposed Biquad Filters (IIR)
│ (Raw PCM time series)
▼
[ 3D Image-Source Acoustic Ray Tracer ]
└── Sparse Tapped-Delay Discrete Convolution
│ (Spatialized wet/dry output)
▼
[ Radix-2 Cooley-Tukey FFT & Spectral Analyzer ]
│ (Verification & ASCII terminal spectrogram)
▼
[ RIFF/WAVE 16-bit PCM Binary Serializer ]
│
▼
output.wav

---

## Core Modules & Mathematical Foundations

### 1. Raw Audio Pipeline (`engine/wav_codec.py`)
- **Canonical Binary Parsing/Serialization**: Custom binary stream parser using `struct` to pack/unpack 16-bit little-endian PCM samples (`fmt ` and `data` chunks) without `wave` or external audio codecs.
- **Dynamic Chunk Traverser**: Traverses arbitrary RIFF chunk hierarchies, safely ignoring metadata tags (`LIST`, `INFO`, `FLLR`) from external DAW/FFmpeg exports.

### 2. DSP & Spectral Analysis (`engine/dsp.py`)
- **Radix-2 Cooley-Tukey FFT**: Implements in-place Decimation-in-Time (DIT) Fast Fourier Transform:
  $$X[k] = \sum_{n=0}^{N-1} x[n] \cdot e^{-j 2\pi k n / N}$$
- Employs bit-reversal permutation and complex exponential twiddle factors without external matrix/linear algebra libraries.
- Features a terminal-native ASCII logarithmic graphic EQ visualizer.

### 3. Sound Synthesis Primitives (`engine/synth.py`)
- **FM Synthesis**: 2-Operator Chowning frequency modulation with dynamic index control:
  $$x(t) = \sin(\omega_c t + I(t) \cdot \sin(\omega_m t))$$
- **Exponential ADSR Envelope**: Time-stepped state machine with asymptotic exponential curves for attack, decay, and release.
- **Direct Form II Transposed Biquad Filter**: Second-order IIR filters derived via Robert Bristow-Johnson pole-zero transforms for resonant lowpass and bandpass behavior.
- **Analog Soft Clipper**: Hyperbolic tangent non-linear waveshaping ($y = \tanh(k \cdot x)$) for tape-style harmonic saturation.

### 4. Algorithmic Composition & Neural Counterpoint (`engine/neural.py`)
- **Bare-Metal Multi-Layer Perceptron (MLP)**: 2-layer neural network trained via pure analytical backpropagation and Cross-Entropy loss.
- Composes modal counterpoint voices (e.g., D-Dorian scale steps) conditioned on a cantus firmus input vector.

### 5. Physical Room Acoustic Modeler (`engine/acoustics.py`)
- **Allen-Berkley Image-Source Ray Tracer**: Simulates specular sound reflections inside a 3D shoebox space:
  $$p(t) = \sum_{r} \frac{\beta^{\vert{}n_x\vert{}+\vert{}n_y\vert{}+\vert{}n_z\vert{}}}{4\pi d_r} \delta\left(t - \frac{d_r}{c}\right)$$
- **Sparse Tapped-Delay Convolution**: Accelerates 1D spatial discrete convolution from $\mathcal{O}(N \times M)$ to $\mathcal{O}(N \times K)$, delivering near-instant execution in interpreted Python.

---

## Project Structure

```text
bare_metal_audio/
├── .vscode/
│   ├── launch.json          # Debugging setup
│   ├── tasks.json           # Integrated terminal tasks
│   └── settings.json        # Editor / Pylance settings
├── engine/
│   ├── __init__.py
│   ├── acoustics.py         # 3D ray tracing & spatial convolution
│   ├── dsp.py               # Radix-2 Cooley-Tukey FFT & magnitude extraction
│   ├── neural.py            # From-scratch MLP neural counterpoint
│   ├── synth.py             # FM oscillators, ADSR envelopes, biquads
│   └── wav_codec.py         # Raw PCM RIFF/WAV binary parser & writer
├── run_engine.py            # Generative synthwave engine & ASCII visualizer
├── remaster_audio.py        # Ingestion pipeline for external WAV spatialization
└── README.md