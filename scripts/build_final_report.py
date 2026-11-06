"""Build the final research report from the recorded experiment outputs."""
import csv
import json
from pathlib import Path

import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "final"
RESULTS = FINAL / "results"
SITE = "https://chenyue-wang-usyd.github.io/elec5305-project-540262760/final/"
REPO = "https://github.com/chenyue-wang-usyd/elec5305-project-540262760"
NAVY = colors.HexColor("#14283c")
TEAL = colors.HexColor("#007969")
PALE = colors.HexColor("#eaf5f1")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=11, leading=16, textColor=NAVY, spaceAfter=11))
styles.add(ParagraphStyle("CaptionSmall", fontName="Helvetica", fontSize=9, leading=13, textColor=NAVY, spaceAfter=12))
styles.add(ParagraphStyle("Kicker", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=TEAL, spaceAfter=14))
styles.add(ParagraphStyle("CoverTitle", fontName="Helvetica-Bold", fontSize=30, leading=34, textColor=NAVY, spaceAfter=17))
styles.add(ParagraphStyle("SectionTitle", fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=NAVY, spaceAfter=16))
styles.add(ParagraphStyle("Formula", fontName="Courier", fontSize=9.5, leading=16, alignment=TA_CENTER, backColor=PALE, borderPadding=8, spaceBefore=5, spaceAfter=15))
story = []


def p(text, style="Body"):
    story.append(Paragraph(text, styles[style]))


def title(number, name):
    story.append(PageBreak())
    p(number, "Kicker")
    p(name, "SectionTitle")


def link(url, name):
    return f'<link href="{url}" color="#007969"><u>{name}</u></link>'


def table(data, widths):
    item = Table(data, colWidths=[w * mm for w in widths], hAlign="LEFT")
    item.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PALE, colors.white]),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend((item, Spacer(1, 12)))


def figure(filename, width):
    image = Image(str(RESULTS / filename))
    image.drawHeight *= width / image.drawWidth
    image.drawWidth = width
    story.append(image)


def footer(canvas, doc):
    canvas.setStrokeColor(PALE)
    canvas.line(22*mm, 17*mm, 188*mm, 17*mm)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(22*mm, 11*mm, "ELEC5305  /  Speech enhancement")
    canvas.drawRightString(188*mm, 11*mm, str(doc.page))


def main():
    result = json.loads((RESULTS / "summary.json").read_text())
    with (RESULTS / "heldout_trials.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    levels = list(result["groups"])
    gains = {m: np.mean([float(r["gain_db"]) for r in rows if r["method"] == m]) for m in ("baseline", "tuned")}
    groups = {}
    for kind in levels:
        groups[kind] = {m: np.mean([float(r["gain_db"]) for r in rows if r["noise"] == kind and r["method"] == m])
                        for m in ("baseline", "tuned")}
    paired = {}
    for row in rows:
        key = (row["utterance"], row["noise"], row["input_snr_db"])
        paired.setdefault(key, {})[row["method"]] = float(row["gain_db"])
    by_speaker = {}
    for (utterance, _, _), scores in paired.items():
        by_speaker.setdefault(utterance.split("-")[0], []).append(scores["tuned"] - scores["baseline"])
    speaker_means = np.array([np.mean(values) for values in by_speaker.values()])
    resamples = np.random.default_rng(617).choice(speaker_means, size=(10000, len(speaker_means)))
    low, high = np.quantile(resamples.mean(axis=1), [.025, .975])
    worst = min((r for r in rows if r["method"] == "tuned"), key=lambda row: float(row["gain_db"]))
    alpha, beta, smooth = result["tuned"]

    story.append(Spacer(1, 17*mm))
    p("ELEC5305  /  FINAL PROJECT  /  2026", "Kicker")
    p("Single-channel speech enhancement with spectral subtraction", "CoverTitle")
    p("Chenyue Wang &nbsp; | &nbsp; Student ID 540262760")
    p("<b>Research question</b><br/>How do over-subtraction, spectral flooring and temporal gain smoothing change the balance between noise reduction and speech distortion across input SNRs and noise conditions?")
    p("<b>Abstract</b><br/>This study compares classical power spectral subtraction with a version tuned on four development speakers. "
      f"Both systems were tested on {result['test_mixtures']} held-out mixtures created from 12 different Mini LibriSpeech speakers. "
      f"Average SNR improvement was {gains['baseline']:+.2f} dB for the baseline and {gains['tuned']:+.2f} dB for the tuned setting. "
      "A noise-only prefix enabled simple noise estimation, and a changing-noise condition tested the consequences of violating the stationary-noise assumption. "
      "The evaluation uses waveform error and an audio example. Perceived quality and intelligibility were outside the measured scope.")
    p(f"{link(SITE, 'Project website')} &nbsp; | &nbsp; {link(REPO, 'Code and reproduction instructions')} &nbsp; | &nbsp; {link(SITE+'demo.mp4', 'Video demonstration')}")
    p("Contents &nbsp; 2 Literature &nbsp; · &nbsp; 3 Methods &nbsp; · &nbsp; 4 Evaluation &nbsp; · &nbsp; 5 Results &nbsp; · &nbsp; 6 Discussion &nbsp; · &nbsp; 7 References", "CaptionSmall")

    title("01  /  INTRODUCTION AND LITERATURE", "From noise estimation to audible artifacts")
    p("A microphone records speech plus sound from the environment. For stationary additive noise, a brief interval before speech can approximate the background spectrum. A single-channel estimator is useful when a second microphone and matched training data are unavailable. It also makes each decision in the enhancement pipeline inspectable.")
    p("<b>Fixed spectral subtraction.</b> Boll [1] estimates background during nonspeech intervals and attenuates spectral components consistent with that estimate. In a power-domain implementation, the additive model motivates subtraction in expectation when speech and noise are uncorrelated. An individual time-frequency bin still contains a cross term, so subtraction can leave isolated peaks or erase weak speech components.")
    p("<b>Gain shaping.</b> Over-subtraction targets more residual noise, while a small floor preserves some energy in deeply attenuated bins. Smoothing the gain over adjacent frames can reduce abrupt changes. All three choices can trade background suppression against consonant or transient loss. The experiment compares the joint effect of tuning these parameters with a fixed classical baseline.")
    p("<b>Adaptive alternatives.</b> Martin [2] estimates noise from minima of smoothed spectral power and is relevant when the noise level changes. This study keeps the fixed prefix estimator in both systems so the gain comparison is interpretable. The changing-noise trial is used to diagnose that design choice.")
    p("<b>Evaluation.</b> Hu and Loizou [3] distinguish speech distortion, background distortion and overall listening quality. A waveform SNR improvement measures a reduction in reference error, while segmental SNR gives low-energy active frames a more equal contribution. Audio and spectrograms supplement these scores without serving as a listening study.")

    title("02  /  SIGNAL PROCESSING", "A common STFT for both methods")
    p("The implementation accepts mono or multichannel WAV, scales integer PCM to floating point and averages channels when needed. A 32 ms Hann window and 8 ms hop give 512 samples per frame and a hop of 128 samples at 16 kHz. The overlap is 75%. SciPy reconstructs the waveform using weighted overlap-add with the same analysis and synthesis settings.")
    p("For bin k and frame m, P(k,m) is squared STFT magnitude. D(k) is the mean of P over complete frames inside the initial 0.5 s noise-only prefix. Excluding boundary-padded frames and frames that straddle speech onset avoids using those bins in the estimate.")
    p("P_target = max(P - alpha D, beta D)", "Formula")
    p("G = clip(sqrt(P_target / max(P, epsilon)), 0, 1)", "Formula")
    p("An optional centered moving average smooths G along time. The final complex spectrum is the smoothed gain times the original noisy STFT. This retains the noisy phase. Clipping prevents gain above unity, and the floor is a target before clipping and smoothing.")
    table([["Method", "Alpha", "Beta", "Smoothing"],
           ["Baseline", "1.0", "0", "1 frame"],
           ["Tuned", str(alpha), str(beta), f"{smooth} frames"]], [53, 32, 33, 46])
    p("<b>Course connection.</b> Week 2 supplies the spectral and power model. Week 4 supplies the STFT and inverse reconstruction. Week 6 motivates the separation of noise estimation from speech enhancement and the use of time-frequency gain masks. Here, the initial silence is provided by design in place of a learned or adaptive VAD.")

    title("03  /  EXPERIMENT DESIGN", "Speaker-disjoint evaluation")
    p("The clean recordings come from Mini LibriSpeech dev-clean-2 [4]. The script sorts archive paths, selects the first usable utterance from each of 16 distinct speakers, and keeps at most six seconds per utterance. The first four speakers are used for development and the remaining 12 are held out. The IDs for both sets are saved in summary.json.")
    p("White noise uses a seeded Gaussian generator. Colored noise uses a one-pole filter with coefficient 0.92. Changing noise uses the same color model but increases in amplitude after the middle of the scored utterance. The tram condition uses deterministic offsets into the Week 4 course recording after mono conversion and resampling. The course recording is kept outside the repository.")
    p("Mixtures prepend 0.5 s of noise only. Noise RMS is calibrated on the region after the prefix to obtain -5, 0, 5, 10 and 15 dB input SNR. The reference and mixture share any peak scaling. Both systems process identical mixtures and are scored only after the prefix.")
    p("The development search tests 27 combinations: alpha in {1, 2, 3}, beta in {0.005, 0.02, 0.05}, and smoothing in {1, 3, 5} frames. Selection maximizes mean output SNR over 24 development mixtures spanning white and colored noise at -5, 5 and 15 dB. All four held-out noise conditions use the same selected configuration.")
    p("Global SNR is 10 log10(reference energy / residual-error energy). For segmental SNR, use nonoverlapping 20 ms frames within 30 dB of the maximum clean frame energy and clip frame scores to [-10, 35] dB before averaging. Runtime factor divides algorithm wall time by processed audio duration. For uncertainty, bootstrap the paired average over 12 speakers rather than treating mixtures from the same speaker as independent.")

    title("04  /  RESULTS", "Gains vary with noise and input level")
    p(f"The tuned setting changed mean SNR improvement by <b>{gains['tuned']-gains['baseline']:+.2f} dB</b> relative to the baseline "
      f"(speaker-bootstrap 95% interval {low:+.2f} to {high:+.2f} dB). Each point below averages 12 held-out utterances.")
    figure("snr.png", 164*mm)
    p("Figure 1. SNR improvement by noise and input SNR. The horizontal line marks equal input and output SNR. Points below it indicate that enhancement increased waveform error.", "CaptionSmall")
    table([["Noise", "Baseline mean", "Tuned mean", "Difference"]] + [
        [kind.capitalize(), f"{groups[kind]['baseline']:+.2f} dB", f"{groups[kind]['tuned']:+.2f} dB",
         f"{groups[kind]['tuned']-groups[kind]['baseline']:+.2f} dB"] for kind in levels], [46, 40, 40, 38])
    seg = {m: np.mean([float(r["segmental_gain_db"]) for r in rows if r["method"] == m]) for m in gains}
    p(f"Mean segmental SNR changes were {seg['baseline']:+.2f} dB and {seg['tuned']:+.2f} dB for baseline and tuned, respectively. "
      f"Median processing factors were {result['median_rtf']['baseline']:.4f} and {result['median_rtf']['tuned']:.4f} on this machine, with file I/O excluded. "
      "This is an offline timing observation. Centered smoothing uses future frames.")

    title("05  /  DISCUSSION AND CONCLUSION", "What the fixed noise estimate misses")
    figure("spectrogram.png", 164*mm)
    p(f"Figure 2. Held-out utterance {result['example']}, colored noise at 0 dB. Panels share a magnitude scale. "
      f"Compare the gaps between speech bursts and weak higher-frequency speech bands. {link(SITE, 'Play the four matched WAV examples')}.", "CaptionSmall")
    p(f"The weakest tuned case was {worst['noise']} noise at {worst['input_snr_db']} dB for utterance {worst['utterance']}, "
      f"with {float(worst['gain_db']):+.2f} dB SNR change. When the starting estimate is too low, noise can remain after a level change. "
      "When subtraction is too strong relative to the local mixture, weak speech can be attenuated. Both effects are consistent with a fixed gain rule operating on uncertain local power estimates.")
    tram = result["groups"].get("tram")
    if tram:
        p("The tram results show a practical trade-off. At 10 dB, the tuned setting gained "
          f"{tram['10']['tuned']['mean_gain_db']:+.2f} dB versus {tram['10']['baseline']['mean_gain_db']:+.2f} dB "
          "for the baseline. At 15 dB, the corresponding gains were "
          f"{tram['15']['tuned']['mean_gain_db']:+.2f} and {tram['15']['baseline']['mean_gain_db']:+.2f} dB. "
          "The quieter interference at these operating points leaves less room for aggressive suppression to offset its speech error.")
    p("The grid selects three settings jointly. It cannot isolate the individual contribution of smoothing or the floor. The held-out corpus contains one read utterance per speaker, and the tram condition uses one recording. Real microphones add reverberation and may have no reliable noise-only prefix. Global and segmental SNR are error measures, so stronger scores do not establish better intelligibility or listener preference.")
    p("The results quantify how one tuned configuration changes the noise-distortion trade-off relative to the classical baseline. A next experiment would compare fixed-prefix estimation with a minimum-statistics or VAD-gated tracker [2], hold the gain rule fixed, and evaluate on additional noise recordings. A listening test could separately rate speech and background distortion as in [3].")

    title("06  /  REFERENCES AND REPRODUCTION", "Sources and experiment files")
    p("[1] S. F. Boll. Suppression of acoustic noise in speech using spectral subtraction. <i>IEEE Transactions on Acoustics, Speech, and Signal Processing</i>, 27(2), 113-120, 1979. " + link("https://doi.org/10.1109/TASSP.1979.1163209", "doi:10.1109/TASSP.1979.1163209"))
    p("[2] R. Martin. Noise power spectral density estimation based on optimal smoothing and minimum statistics. <i>IEEE Transactions on Speech and Audio Processing</i>, 9(5), 504-512, 2001. " + link("https://doi.org/10.1109/89.928915", "doi:10.1109/89.928915"))
    p("[3] Y. Hu and P. C. Loizou. Evaluation of objective measures for speech enhancement. <i>Interspeech</i>, 2006. " + link("https://www.isca-archive.org/interspeech_2006/hu06_interspeech.html", "ISCA Archive"))
    p("[4] OpenSLR. Mini LibriSpeech ASR corpus, SLR31, CC BY 4.0. " + link("https://openslr.org/31/", "Archive and licence") + ". The demonstration excerpt is truncated and level-adjusted. Noise and enhancement are added in the derived versions.")
    p("<b>Reproduce the experiment.</b> Install requirements.txt and run scripts/evaluate_final.py with the official dev-clean-2.tar.gz archive. Add --recorded-noise pointing to the Week 4 tram.wav to reproduce the tram condition. Final output files include a complete development grid, held-out trial CSV, summary JSON, plots and matched audio.")
    p(f"{link(REPO, 'Source repository')} &nbsp; | &nbsp; {link(SITE, 'Project website')} &nbsp; | &nbsp; {link(SITE+'demo.mp4', 'Video demonstration')}")
    p("<b>AI use declaration.</b> OpenAI ChatGPT and Codex assisted with implementation, experimental design, running and interpreting experiments, report drafting and formatting, and preparing the demonstration. The video uses synthetic narration. Numerical results were computed by the accompanying code. The student is responsible for reviewing and explaining the work and confirming course requirements before submission.")

    document = SimpleDocTemplate(str(FINAL / "ELEC5305_Final_Project_Report.pdf"),
                                 pagesize=(210*mm, 297*mm), leftMargin=22*mm, rightMargin=22*mm,
                                 topMargin=23*mm, bottomMargin=24*mm,
                                 title="Single-channel speech enhancement with spectral subtraction", author="Chenyue Wang")
    document.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    main()
