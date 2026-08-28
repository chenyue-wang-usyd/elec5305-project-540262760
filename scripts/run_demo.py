"""Create a deterministic speech-like denoising demonstration and figures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import spectrogram

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.spectral_subtraction import spectral_subtract, write_wav  # noqa: E402


def snr_db(clean: np.ndarray, estimate: np.ndarray, mask: np.ndarray) -> float:
    reference = clean[mask]
    error = estimate[mask] - reference
    return float(10.0 * np.log10(np.sum(reference**2) / np.sum(error**2)))


def make_demo(sample_rate: int = 16000) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    duration = 4.0
    t = np.arange(int(sample_rate * duration)) / sample_rate
    active = t >= 0.5
    ta = np.maximum(t - 0.5, 0.0)

    syllables = np.maximum(0.0, np.sin(2 * np.pi * 2.2 * ta)) ** 0.65
    onset = np.clip((t - 0.5) / 0.08, 0.0, 1.0)
    offset = np.clip((duration - t) / 0.12, 0.0, 1.0)
    envelope = active * syllables * onset * offset
    f0 = 125.0 + 22.0 * np.sin(2 * np.pi * 0.7 * ta)
    phase = 2 * np.pi * np.cumsum(f0) / sample_rate
    voiced = sum((1.0 / h) * np.sin(h * phase) for h in range(1, 9))
    formant = 0.55 * np.sin(2 * np.pi * 700 * t) + 0.28 * np.sin(2 * np.pi * 1200 * t)
    clean = 0.16 * envelope * (voiced + 0.18 * formant)

    rng = np.random.default_rng(5305)
    white = rng.standard_normal(len(t))
    coloured = np.empty_like(white)
    coloured[0] = white[0]
    for i in range(1, len(white)):
        coloured[i] = 0.94 * coloured[i - 1] + white[i]
    coloured -= np.mean(coloured)
    coloured /= np.std(coloured)

    clean_rms = np.sqrt(np.mean(clean[active] ** 2))
    noise = coloured * clean_rms
    noisy = clean + noise
    return t, clean, noisy, active


def save_figures(t: np.ndarray, clean: np.ndarray, noisy: np.ndarray, enhanced: np.ndarray, sample_rate: int) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(10, 6.5), sharex=True)
    for ax, signal, title, colour in zip(
        axes,
        (clean, noisy, enhanced),
        ("Clean reference", "Noisy mixture (0 dB)", "Enhanced output"),
        ("#1f77b4", "#d95f02", "#2a9d8f"),
    ):
        ax.plot(t, signal, color=colour, linewidth=0.7)
        ax.set_ylabel("Amplitude")
        ax.set_title(title, loc="left", fontsize=10, weight="bold")
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "waveforms.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(10, 7.2), sharex=True, sharey=True)
    for ax, signal, title in zip(axes, (clean, noisy, enhanced), ("Clean", "Noisy", "Enhanced")):
        f, tt, sxx = spectrogram(signal, sample_rate, nperseg=512, noverlap=384, mode="magnitude")
        db = 20 * np.log10(np.maximum(sxx, 1e-8))
        ax.pcolormesh(tt, f / 1000.0, db, shading="auto", cmap="magma", vmin=-90, vmax=-25)
        ax.set_ylim(0, 4)
        ax.set_ylabel("kHz")
        ax.set_title(title, loc="left", fontsize=10, weight="bold")
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "spectrograms.png", dpi=180)
    plt.close(fig)


def main() -> None:
    sample_rate = 16000
    results = ROOT / "results"
    results.mkdir(parents=True, exist_ok=True)
    t, clean, noisy, active = make_demo(sample_rate)
    enhanced = spectral_subtract(
        noisy,
        sample_rate,
        noise_duration=0.5,
        alpha=2.0,
        beta=0.02,
        frame_ms=32,
        hop_ms=8,
        gain_smoothing=3,
    )

    input_snr = snr_db(clean, noisy, active)
    output_snr = snr_db(clean, enhanced, active)
    metrics = {
        "sample_rate_hz": sample_rate,
        "input_snr_db": round(input_snr, 3),
        "output_snr_db": round(output_snr, 3),
        "snr_improvement_db": round(output_snr - input_snr, 3),
        "alpha": 2.0,
        "beta": 0.02,
        "noise_duration_s": 0.5,
        "gain_smoothing_frames": 3,
    }

    write_wav(results / "demo_clean.wav", sample_rate, clean)
    write_wav(results / "demo_noisy_0db.wav", sample_rate, noisy)
    write_wav(results / "demo_enhanced.wav", sample_rate, enhanced)
    (results / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    save_figures(t, clean, noisy, enhanced, sample_rate)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

