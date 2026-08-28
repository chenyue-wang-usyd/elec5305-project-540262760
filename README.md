# Audio Noise Reduction Using Spectral Subtraction

ELEC5305 project proposal and reproducible Python prototype for single-channel audio noise reduction. The system estimates a noise spectrum from an initial noise-only segment, applies power spectral subtraction with over-subtraction and spectral flooring, then reconstructs the signal with the noisy phase.

## Repository contents

- `proposal/ELEC5305_Audio_Noise_Reduction_Proposal.pdf` - submission-ready proposal draft
- `proposal/proposal.md` - editable proposal source
- `src/spectral_subtraction.py` - reusable implementation and WAV command-line interface
- `scripts/run_demo.py` - deterministic synthetic experiment
- `tests/test_spectral_subtraction.py` - automated correctness and performance checks
- `results/` - generated WAV files, figures, and metrics
- `index.html` - GitHub Pages project summary

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

## Evaluation plan

The final study will evaluate white and coloured noise at input SNRs from -5 dB to 15 dB. Reported measures will include global SNR improvement, segmental SNR, optional STOI/PESQ when available, runtime, and spectrogram/listening comparisons. The classical method will be compared with over-subtraction, spectral flooring, and time-smoothed gain variants.

## Submission details

- Student: Chenyue Wang
- SID: 540262760
- GitHub repository: https://github.com/chenyue-wang-usyd/elec5305-project-540262760
- GitHub Pages: https://chenyue-wang-usyd.github.io/elec5305-project-540262760/

After publishing, confirm that the repository is public and that GitHub Pages is deployed from the `main` branch.

## AI use declaration

Generative AI tools (OpenAI ChatGPT and Codex) were used to assist with project planning, organising the literature search, drafting, Python implementation, debugging, documentation, and document formatting. I reviewed and revised all AI-assisted material, verified the references against publication sources, executed the code and tests, and checked the reported outputs. I remain responsible for the accuracy and integrity of the final submission. The preliminary 5.73 dB SNR improvement was produced by the deterministic local experiment in this repository; it is not an AI-generated result or a claim about real-speech performance.
