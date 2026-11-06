# Audio Noise Reduction Using Spectral Subtraction

ELEC5305 project proposal and reproducible Python prototype for single-channel audio noise reduction. The system estimates a noise spectrum from an initial noise-only segment, applies power spectral subtraction with over-subtraction and spectral flooring, then reconstructs the signal with the noisy phase.

## Final project

- [Project page, report, demonstration and audio samples](final/index.html)
- [Research report (PDF)](final/ELEC5305_Final_Project_Report.pdf)
- [Video demonstration (MP4)](final/demo.mp4)
- [Trial-level results](final/results/heldout_trials.csv) and [parameter grid](final/results/development_grid.csv)

The final evaluation uses 16 distinct speakers from the official [Mini LibriSpeech dev-clean-2 archive](https://openslr.org/31/) (CC BY 4.0). Four speakers are used to select the parameters, and twelve different speakers are used only for the held-out evaluation. Download the archive, then run:

```bash
pip install -r requirements.txt
python scripts/evaluate_final.py dev-clean-2.tar.gz --recorded-noise path/to/tram.wav
python -m unittest discover -s tests -v
```

Use the ELEC5305 Week 4 tram.wav for the fourth condition. Omit the flag if you do not have the course recording. The reproducible synthetic-noise conditions use deterministic seeds and are otherwise unaffected. The course recording is not redistributed. The held-out CSV includes timings that vary with the machine. The website audio excerpt is truncated and level-adjusted, with added noise or enhancement as indicated. The report includes an AI use declaration, and the demonstration uses synthetic narration.

Rebuild the PDF with `pip install reportlab` and `python scripts/build_final_report.py`. Rebuild the narrated MP4 with `pip install edge-tts` and `python scripts/build_final_video.py` after regenerating the experiment outputs. The narration uses Andrew, a US English voice and requires an internet connection.

## Audio Processing Report 2

**Extracting a Musical Foreground from Stereo Ambience** - an English MATLAB report applying Week 6 overlap-add processing and Week 8 stereo decomposition.

- [Download the complete submission ZIP](reports/report2/Report2%20ChenyueWang.zip)
- [Read the report PDF](reports/report2/Report2%20ChenyueWang/Report2%20ChenyueWang.pdf)
- [Open the MATLAB Live Script](reports/report2/Report2%20ChenyueWang/Report2%20ChenyueWang.mlx)
- [Reproduction instructions and source files](reports/report2/Report2%20ChenyueWang/README.md)

Validated in MATLAB R2026a. All 45 trials and the audio outputs reproduced exactly after extracting the final ZIP into a separate folder. The report includes references and an AI use declaration.

## Repository contents

- `proposal/ELEC5305_Audio_Noise_Reduction_Proposal.pdf` - submission-ready proposal draft
- `proposal/proposal.md` - editable proposal source
- `src/spectral_subtraction.py` - reusable implementation and WAV command-line interface
- `scripts/run_demo.py` - deterministic synthetic experiment
- `tests/test_spectral_subtraction.py` - automated correctness and performance checks
- `results/` - generated WAV files, figures, and metrics
- `index.html` - GitHub Pages project summary
- `WALKTHROUGH.md` - English explanation of the algorithm, results, and remaining work

## Quick start

Python 3.10 or later is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_demo.py
python -m unittest discover -s tests -v
```

The demo writes a clean reference, a 0 dB noisy mixture, the enhanced output, objective metrics, and waveform/spectrogram figures to `results/`.

## Process your own WAV file

The first part of the input must contain noise only so that the noise power spectrum can be estimated.

```bash
python src/spectral_subtraction.py input.wav output.wav --noise-duration 0.5 --alpha 2.0 --beta 0.02
```

Important options:

- `--noise-duration`: duration in seconds of the initial noise-only region
- `--alpha`: over-subtraction factor; larger values remove more noise but may distort speech
- `--beta`: spectral floor relative to estimated noise power; helps reduce musical noise
- `--frame-ms` and `--hop-ms`: STFT frame and hop sizes
- `--gain-smoothing`: number of frames used to smooth the gain over time

## Submission details

- Student: Chenyue Wang
- SID: 540262760
- GitHub repository: https://github.com/chenyue-wang-usyd/elec5305-project-540262760
- GitHub Pages: https://chenyue-wang-usyd.github.io/elec5305-project-540262760/

After publishing, confirm that the repository is public and that GitHub Pages is deployed from the `main` branch.

## AI use declaration

OpenAI ChatGPT and Codex assisted with drafting, implementation, debugging, reference checks, and formatting. Synthetic metrics are computed by the supplied code. The student remains responsible for reviewing the material and complying with course requirements before submission. The preliminary 5.73 dB SNR improvement comes from a deterministic synthetic experiment; it does not establish real-speech performance.
