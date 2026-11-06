"""Render a short, narrated demonstration using the experiment and actual CLI output."""
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

import edge_tts
import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "final"
RESULTS = FINAL / "results"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "en-US-AndrewMultilingualNeural"


def ffmpeg(*args):
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], check=True)


def slide(path, label, title, lines, figure=None):
    canvas = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor="#102639")
    canvas.text(.055, .91, label, color="#81e2ce", fontsize=15, weight="bold")
    canvas.text(.055, .80, title, color="white", fontsize=30, weight="bold")
    if figure:
        ax = canvas.add_axes([.055, .20, .89, .51])
        ax.imshow(plt.imread(figure))
        ax.axis("off")
        ypos = .13
        spacing = .05
    else:
        ypos = .64
        spacing = .10
    for i, line in enumerate(lines):
        canvas.text(.058, ypos-i*spacing, line, fontsize=16 if figure else 19, color="#e5f0f7")
    canvas.text(.055, .038, "ELEC5305  /  FINAL PROJECT", fontsize=11, color="#81e2ce")
    canvas.savefig(path, facecolor=canvas.get_facecolor())
    plt.close(canvas)


def main():
    with TemporaryDirectory(prefix="elec5305-video-") as folder:
        temp = Path(folder)
        cli = subprocess.run([sys.executable, "src/spectral_subtraction.py",
                              "final/results/noisy.wav", str(temp/"enhanced.wav"),
                              "--alpha", "3", "--beta", "0.005", "--gain-smoothing", "3"],
                             cwd=ROOT, check=True, text=True, capture_output=True)
        assert (temp/"enhanced.wav").stat().st_size > 1000 and "16000 Hz" in cli.stdout
        chapters = [
            ("01  /  RESEARCH QUESTION", "Can tuning improve noise reduction?",
             ["Single-channel speech enhancement with spectral subtraction",
              "Compare a classical baseline against a tuned gain rule.",
              "12 held-out speakers, 4 noise conditions, 5 input SNRs."], None,
             "How much background noise can we remove before we start losing parts of the speech? To find out, this project compares a standard spectral subtraction method with a version tuned on a separate group of speakers.", None),
            ("02  /  METHOD", "Estimate noise, shape gain, reconstruct",
             ["32 ms Hann analysis window  /  8 ms hop",
              "Estimate noise power using the first 0.5 seconds.",
              "Subtract power, apply a floor and smooth gain over time.",
              "Retain noisy phase and reconstruct with inverse STFT."], None,
             "The first half second contains only background noise. That gives us a starting estimate of its spectrum. A short-time Fourier transform splits the recording into overlapping frames. We subtract estimated noise power, apply a spectral floor, and smooth the gain across frames. Then we reconstruct the audio using the original phase.", None),
            ("03  /  CODE IN ACTION", "Run the WAV command-line tool",
             ["python src/spectral_subtraction.py noisy.wav enhanced.wav",
              "  --alpha 3 --beta 0.005 --gain-smoothing 3",
              cli.stdout.strip().split(" (")[-1].rstrip(")") + "  /  output WAV verified"], None,
             "Here is the command used for this example. It takes the noisy recording and writes an enhanced wave file. In the next two clips, you will hear the same excerpt at the same playback level. First comes the noisy input, followed by the enhanced output.", None),
            ("04  /  LISTENING DEMO", "Noisy input  |  colored noise at 0 dB",
             ["Mini LibriSpeech excerpt 1993-147964-0000."], RESULTS/"spectrogram.png", None, RESULTS/"noisy.wav"),
            ("05  /  LISTENING DEMO", "Enhanced output  |  tuned settings",
             ["Same excerpt. The fourth panel shows the tuned result."], RESULTS/"spectrogram.png", None, temp/"enhanced.wav"),
            ("06  /  HELD-OUT RESULTS", "Strongest gains in stationary noise",
             ["Average SNR improvement: baseline +2.41 dB, tuned +4.73 dB.",
              "The tuned method trailed the baseline for tram noise at 10 and 15 dB."], RESULTS/"snr.png",
             "Across two hundred and forty held-out mixtures, the tuned method improved the signal-to-noise ratio by four point seven three decibels on average. The baseline gained two point four one decibels. The biggest gains were in steady noise. With tram noise at ten and fifteen decibels, the baseline did slightly better. These scores measure how closely the output matches the clean reference. Listener preference would need a separate test.", None),
        ]
        clips = []
        for i, (label,title,lines,figure,spoken,recording) in enumerate(chapters):
            frame = temp/f"{i}.png"
            slide(frame,label,title,lines,figure)
            if spoken:
                if re.search(r"\d", spoken):
                    raise ValueError("Spell out all narration numbers in English.")
                recording = temp/f"{i}.mp3"
                edge_tts.Communicate(spoken, VOICE, rate="-6%").save_sync(str(recording))
            clip = temp/f"{i}.mp4"
            ffmpeg("-loop", "1", "-framerate", "25", "-i", frame, "-i", recording,
                   "-af", "apad=pad_dur=0.35", "-shortest", "-c:v", "libx264",
                   "-preset", "fast", "-crf", "21", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-ac", "1", "-ar", "48000", clip)
            clips.append(clip)
        playlist = temp/"clips.txt"
        playlist.write_text("\n".join(f"file '{clip.name}'" for clip in clips), encoding="utf-8")
        rendered = temp/"demo.mp4"
        ffmpeg("-f", "concat", "-safe", "0", "-i", playlist, "-c", "copy",
               "-movflags", "+faststart", rendered)
        ffmpeg("-i", rendered, "-f", "null", "-")
        rendered.replace(FINAL/"demo.mp4")


if __name__ == "__main__":
    main()
