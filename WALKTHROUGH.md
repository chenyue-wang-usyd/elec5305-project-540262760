# Project walkthrough

## What this submission contains

The supplied ELEC5305 guide requests a 700-1000-word **project proposal**. This repository contains that proposal, an initial working prototype, a synthetic demonstration, and a GitHub Pages summary. It is not a completed experimental study of real speech.

The proposal covers the problem, motivation, signal-processing method, evaluation plan, expected deliverables, a 13-week timeline, and three peer-reviewed references. The project uses classical spectral subtraction; it does not train a neural network. Noise tracking based on minimum statistics is a possible extension, not an implemented feature.

## How the algorithm works

1. **Read and scale audio.** Convert integer PCM samples to floating point, centre unsigned 8-bit PCM around zero, and average multiple channels. Scaling before channel averaging preserves the intended amplitude.
2. **Split the recording into overlapping frames.** At 16 kHz, a 32 ms frame contains 512 samples and an 8 ms hop advances 128 samples. A Hann window reduces frame-boundary discontinuities.
3. **Compute the STFT.** Each frame becomes a complex spectrum showing frequency content and phase. Squared magnitude gives a power spectrum.
4. **Estimate background noise.** Average spectral power from frames whose centres fall within the first 0.5 seconds. The recording must begin with noise alone. Frames near the boundary can include later samples, so leave a margin before speech starts. The current estimate stays fixed during the recording.
5. **Subtract estimated noise power.** The target is `max(observed_power - alpha * noise_power, beta * noise_power)`. Increasing `alpha` removes more noise but can damage speech. `beta` keeps a residual floor to limit isolated musical-noise artefacts.
6. **Apply a bounded, smoothed gain.** Convert target power to amplitude gain, cap it at one, and smooth across frames. The cap and smoothing mean the target floor is not an exact output-power guarantee. The implementation uses centred smoothing, so it is an offline processor rather than a demonstrated causal streaming system.
7. **Reconstruct and save.** Retain the noisy phase, apply inverse STFT and overlap-add, and save the enhanced WAV. If necessary, the WAV writer scales peaks down to avoid clipping.

## What the demonstration establishes

Run these commands from the repository root after installing Python and the requirements:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/run_demo.py
```

The demo creates four seconds of synthetic speech-like harmonic audio with coloured stationary noise. Its first half-second contains noise only. A fixed random seed makes the experiment repeatable.

| Measurement | Reproduced value |
|---|---:|
| Input SNR | 0.094 dB |
| Output SNR | 5.827 dB |
| Improvement | 5.733 dB |

SNR compares reference signal energy with error energy: `10 * log10(sum(clean**2) / sum((estimate-clean)**2))`. Scoring uses the region after 0.5 seconds, including internal pauses. The WAV filename says `0db`, but the measured input is 0.094 dB because noise is normalised over the whole recording while SNR is measured over the later region.

The improvement demonstrates that this configuration reduces error on this synthetic example. It does not prove improved intelligibility, universal noise removal, or the same performance on real speech. Listen to `demo_noisy_0db.wav` and `demo_enhanced.wav` at the same playback volume and compare them with `demo_clean.wav`. The spectrogram shows where energy changes over time and frequency.

## What was corrected in this revision

- Condensed the proposal and checked the complete PDF against the word limit, rather than counting only selected body sections.
- Removed “adaptive” from the title because the current noise estimate is fixed.
- Explained gain clipping and smoothing so the proposal matches the code.
- Fixed stereo integer PCM scaling and unsigned 8-bit centring, with regression tests. All five tests pass.
- Retained three verified references and removed an unverified page range from the Hu and Loizou citation.
- Reworded the AI declaration so it does not claim the student has already performed checks that the assistant cannot establish.

## Remaining work for the full project

Obtain and document suitable speech/noise data, separate tuning and evaluation utterances, calibrate each mixture over its scored region, and compare variants across noise types and SNR levels. Implement segmental SNR and runtime measurement; add STOI/PESQ if feasible. Report failures and listening observations alongside numerical gains. These are proposed experiments, not results already achieved.

Before submission, read the proposal and ensure the explanations, attribution, and AI declaration accurately reflect your own understanding and course requirements.
