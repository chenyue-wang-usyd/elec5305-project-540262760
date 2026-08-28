"""Single-channel power spectral subtraction with a command-line WAV interface."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d
from scipy.signal import istft, stft


def _to_float_mono(samples: np.ndarray) -> np.ndarray:
    """Convert integer/float mono or stereo audio to finite float64 mono audio."""
    audio = np.asarray(samples)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if audio.ndim != 1:
        raise ValueError("Audio must be mono or two-dimensional multichannel data")
    if np.issubdtype(audio.dtype, np.integer):
        limit = max(abs(np.iinfo(audio.dtype).min), np.iinfo(audio.dtype).max)
        audio = audio.astype(np.float64) / float(limit)
    else:
        audio = audio.astype(np.float64)
    if not np.all(np.isfinite(audio)):
        raise ValueError("Audio contains NaN or infinite values")
    return audio


def spectral_subtract(
    noisy: np.ndarray,
    sample_rate: int,
    *,
    noise_duration: float = 0.5,
    alpha: float = 2.0,
    beta: float = 0.02,
    frame_ms: float = 32.0,
    hop_ms: float = 8.0,
    gain_smoothing: int = 3,
) -> np.ndarray:
    """Enhance a signal using a noise estimate from its initial noise-only region.

    Args:
        noisy: One-dimensional noisy signal in an arbitrary finite scale.
        sample_rate: Positive sampling rate in hertz.
        noise_duration: Initial noise-only duration in seconds.
        alpha: Power over-subtraction factor, at least 1.
        beta: Non-negative spectral floor relative to estimated noise power.
        frame_ms: STFT frame length in milliseconds.
        hop_ms: STFT hop length in milliseconds.
        gain_smoothing: Odd/even positive count of frames for temporal smoothing.
    """
    x = _to_float_mono(noisy)
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if len(x) < 2:
        raise ValueError("Audio must contain at least two samples")
    if noise_duration <= 0:
        raise ValueError("noise_duration must be positive")
    if alpha < 1:
        raise ValueError("alpha must be at least 1")
    if beta < 0:
        raise ValueError("beta must be non-negative")
    if gain_smoothing < 1:
        raise ValueError("gain_smoothing must be at least 1")

    nperseg = max(16, int(round(frame_ms * sample_rate / 1000.0)))
    nperseg = min(nperseg, len(x))
    hop = max(1, int(round(hop_ms * sample_rate / 1000.0)))
    if hop >= nperseg:
        raise ValueError("hop_ms must be smaller than frame_ms")
    noverlap = nperseg - hop

    _, times, spectrum = stft(
        x,
        fs=sample_rate,
        window="hann",
        nperseg=nperseg,
        noverlap=noverlap,
        boundary="zeros",
        padded=True,
    )
    power = np.abs(spectrum) ** 2
    noise_frames = times <= noise_duration
    if not np.any(noise_frames):
        noise_frames[0] = True
    noise_psd = np.mean(power[:, noise_frames], axis=1, keepdims=True)

    eps = np.finfo(np.float64).eps
    enhanced_power = np.maximum(power - alpha * noise_psd, beta * noise_psd)
    gain = np.sqrt(enhanced_power / np.maximum(power, eps))
    gain = np.clip(gain, 0.0, 1.0)
    if gain_smoothing > 1:
        gain = uniform_filter1d(gain, size=gain_smoothing, axis=1, mode="nearest")

    enhanced_spectrum = gain * spectrum
    _, enhanced = istft(
        enhanced_spectrum,
        fs=sample_rate,
        window="hann",
        nperseg=nperseg,
        noverlap=noverlap,
        input_onesided=True,
        boundary=True,
    )
    enhanced = enhanced[: len(x)]
    if len(enhanced) < len(x):
        enhanced = np.pad(enhanced, (0, len(x) - len(enhanced)))
    return enhanced.astype(np.float64, copy=False)


def read_wav(path: Path) -> tuple[int, np.ndarray]:
    sample_rate, samples = wavfile.read(path)
    return int(sample_rate), _to_float_mono(samples)


def write_wav(path: Path, sample_rate: int, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.asarray(samples, dtype=np.float64)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0.999:
        audio = audio * (0.999 / peak)
    wavfile.write(path, sample_rate, np.asarray(audio, dtype=np.float32))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input noisy WAV")
    parser.add_argument("output", type=Path, help="output enhanced WAV")
    parser.add_argument("--noise-duration", type=float, default=0.5)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--beta", type=float, default=0.02)
    parser.add_argument("--frame-ms", type=float, default=32.0)
    parser.add_argument("--hop-ms", type=float, default=8.0)
    parser.add_argument("--gain-smoothing", type=int, default=3)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    sample_rate, noisy = read_wav(args.input)
    enhanced = spectral_subtract(
        noisy,
        sample_rate,
        noise_duration=args.noise_duration,
        alpha=args.alpha,
        beta=args.beta,
        frame_ms=args.frame_ms,
        hop_ms=args.hop_ms,
        gain_smoothing=args.gain_smoothing,
    )
    write_wav(args.output, sample_rate, enhanced)
    print(f"Wrote {args.output} ({len(enhanced) / sample_rate:.2f} s at {sample_rate} Hz)")


if __name__ == "__main__":
    main()

