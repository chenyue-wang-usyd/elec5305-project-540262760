"""Evaluate spectral subtraction on a speaker-disjoint Mini LibriSpeech subset."""
import argparse
import csv
import io
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from time import perf_counter

import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter, resample_poly, stft

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.spectral_subtraction import read_wav, spectral_subtract

RATE = 16000
PREFIX = RATE // 2
SNRS = (-5, 0, 5, 10, 15)
BASELINE = (1.0, 0.0, 1)


def speech_subset(archive):
    """Select one utterance per speaker, reproducibly, from the official archive."""
    speakers = {}
    with tarfile.open(archive, "r:gz") as corpus:
        for member in sorted(corpus.getmembers(), key=lambda item: item.name):
            if not member.isfile() or not member.name.endswith(".flac"):
                continue
            utterance = Path(member.name).stem
            speaker = utterance.split("-")[0]
            if speaker in speakers or len(speakers) == 16:
                continue
            raw = corpus.extractfile(member).read()
            result = subprocess.run(
                [imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", "pipe:0",
                 "-ac", "1", "-ar", str(RATE), "-f", "f32le", "pipe:1"],
                input=raw, capture_output=True, check=True,
            )
            signal = np.frombuffer(result.stdout, dtype="<f4").astype(float)
            if len(signal) >= 2 * RATE:
                speakers[speaker] = (utterance, signal[:6 * RATE])
    if len(speakers) != 16:
        raise ValueError("Expected 16 distinct speakers with usable utterances")
    return list(speakers.values())


def mixture(speech, kind, snr_db, seed, recorded):
    rng = np.random.default_rng(seed)
    speech = speech * (0.35 / np.max(np.abs(speech)))
    clean = np.pad(speech, (PREFIX, 0))
    noise = rng.standard_normal(len(clean))
    if kind in ("colored", "changing"):
        noise = lfilter([1], [1, -0.92], noise)
    if kind == "changing":
        noise[:PREFIX + len(speech) // 2] *= 0.3
    if kind == "tram":
        offset = rng.integers(len(recorded))
        noise = recorded[(offset + np.arange(len(clean))) % len(recorded)].copy()
        noise -= noise.mean()
    gain = np.linalg.norm(speech) / np.linalg.norm(noise[PREFIX:]) * 10 ** (-snr_db / 20)
    noisy = clean + gain * noise
    scale = 0.98 / max(0.98, np.max(np.abs(noisy)))
    return clean * scale, noisy * scale


def score(reference, estimate):
    error = reference - estimate
    global_snr = 10 * np.log10(np.sum(reference ** 2) / max(1e-15, np.sum(error ** 2)))
    frame = 320
    length = len(reference) // frame * frame
    clean_power = (reference[:length].reshape(-1, frame) ** 2).sum(axis=1)
    error_power = (error[:length].reshape(-1, frame) ** 2).sum(axis=1)
    active = clean_power >= clean_power.max() * 1e-3
    segments = 10 * np.log10((clean_power[active] + 1e-15) / (error_power[active] + 1e-15))
    return global_snr, np.clip(segments, -10, 35).mean()


def process(noisy, config):
    alpha, beta, smoothing = config
    return spectral_subtract(noisy, RATE, alpha=alpha, beta=beta, gain_smoothing=smoothing)


def write_csv(path, records):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def figures(output, summary, example):
    fig, axs = plt.subplots(1, len(summary), figsize=(3.05 * len(summary), 3.4), sharey=True)
    for ax, (kind, levels) in zip(np.atleast_1d(axs), summary.items()):
        for method, color in (("baseline", "#8592a4"), ("tuned", "#007969")):
            ax.plot(SNRS, [levels[str(s)][method]["mean_gain_db"] for s in SNRS],
                    marker="o", color=color, label=method.capitalize())
        ax.axhline(0, color="#333333", linewidth=.6)
        ax.set(title=kind.capitalize(), xlabel="Input SNR (dB)", xticks=SNRS)
        ax.grid(alpha=.2)
    axs[0].set_ylabel("Mean SNR improvement (dB)")
    axs[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "snr.png", dpi=175)
    plt.close(fig)
    fig, axs = plt.subplots(1, 4, figsize=(11, 3), sharey=True)
    spectra = [stft(signal, RATE, nperseg=512, noverlap=384) for signal in example]
    peak = max(np.abs(spectrum).max() for _, _, spectrum in spectra)
    for ax, label, (freqs, times, spectrum) in zip(axs, ("Clean", "Noisy", "Baseline", "Tuned"), spectra):
        db = 20 * np.log10(np.maximum(np.abs(spectrum) / peak, 1e-5))
        mesh = ax.pcolormesh(times, freqs / 1000, db, vmin=-65, vmax=0, shading="auto", cmap="magma")
        ax.set(title=label, xlabel="Seconds", ylim=(0, 6))
    axs[0].set_ylabel("Frequency (kHz)")
    fig.subplots_adjust(left=.07, right=.9, bottom=.19, top=.88, wspace=.14)
    fig.colorbar(mesh, cax=fig.add_axes([.92, .19, .015, .69]), label="dB relative to common peak")
    fig.savefig(output / "spectrogram.png", dpi=175)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="OpenSLR SLR31 dev-clean-2.tar.gz")
    parser.add_argument("--recorded-noise", type=Path, help="Optional ELEC5305 Week 4 tram.wav")
    parser.add_argument("--output", type=Path, default=Path("final/results"))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    corpus = speech_subset(args.archive)
    kinds = ["white", "colored", "changing"]
    recorded = None
    if args.recorded_noise:
        rate, recorded = read_wav(args.recorded_noise)
        recorded = resample_poly(recorded, RATE, rate)
        kinds.append("tram")

    # Select settings only on the four development speakers and stationary noises.
    dev = []
    for i, (_, speech) in enumerate(corpus[:4]):
        for j, kind in enumerate(kinds[:2]):
            for snr in (-5, 5, 15):
                dev.append(mixture(speech, kind, snr, 1000 + 10 * i + j, recorded))
    grid = []
    for config in itertools.product((1., 2., 3.), (.005, .02, .05), (1, 3, 5)):
        values = [score(clean[PREFIX:], process(noisy, config)[PREFIX:])[0] for clean, noisy in dev]
        grid.append(dict(alpha=config[0], beta=config[1], smoothing=config[2], mean_output_snr=np.mean(values)))
    grid.sort(key=lambda row: -row["mean_output_snr"])
    winner = tuple(grid[0][k] for k in ("alpha", "beta", "smoothing"))
    write_csv(out / "development_grid.csv", grid)

    rows = []
    example = None
    for i, (uid, speech) in enumerate(corpus[4:]):
        for j, kind in enumerate(kinds):
            for snr in SNRS:
                clean, noisy = mixture(speech, kind, snr, 2000 + 10 * i + j, recorded)
                input_snr, input_seg = score(clean[PREFIX:], noisy[PREFIX:])
                outputs = []
                for method, config in (("baseline", BASELINE), ("tuned", winner)):
                    start = perf_counter()
                    enhanced = process(noisy, config)
                    runtime = perf_counter() - start
                    outputs.append(enhanced)
                    snr_out, seg = score(clean[PREFIX:], enhanced[PREFIX:])
                    rows.append(dict(utterance=uid, noise=kind, input_snr_db=snr,
                                     method=method, gain_db=snr_out - input_snr,
                                     segmental_gain_db=seg - input_seg,
                                     real_time_factor=runtime / (len(noisy) / RATE)))
                if i == 0 and kind == "colored" and snr == 0:
                    example = (clean, noisy, *outputs)
                    for label, audio in zip(("clean", "noisy", "baseline", "tuned"), example):
                        wavfile.write(out / f"{label}.wav", RATE, (np.clip(audio, -1, 1) * 32767).astype("<i2"))
    write_csv(out / "heldout_trials.csv", rows)
    summary = {}
    for kind in kinds:
        summary[kind] = {}
        for snr in SNRS:
            summary[kind][str(snr)] = {}
            for method in ("baseline", "tuned"):
                selected = [r for r in rows if (r["noise"], r["input_snr_db"], r["method"]) == (kind, snr, method)]
                summary[kind][str(snr)][method] = {
                    "mean_gain_db": float(np.mean([r["gain_db"] for r in selected])),
                    "mean_segmental_gain_db": float(np.mean([r["segmental_gain_db"] for r in selected])),
                    "n": len(selected),
                }
    metadata = dict(baseline=BASELINE, tuned=winner, test_mixtures=len(rows)//2, example=corpus[4][0],
                    development=[uid for uid, _ in corpus[:4]], test=[uid for uid, _ in corpus[4:]],
                    median_rtf={m: float(np.median([r["real_time_factor"] for r in rows if r["method"] == m]))
                                for m in ("baseline", "tuned")},
                    groups=summary)
    (out / "summary.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    figures(out, summary, example)
    print(f"Evaluated {len(rows)//2} held-out mixtures. Baseline {BASELINE}; selected {winner}.")


if __name__ == "__main__":
    main()
