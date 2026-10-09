# Single-Channel Audio Noise Reduction Using Spectral Subtraction

## Student Information

- Full Name: **Chenyue Wang**
- Student ID (SID): **540262760**
- GitHub Username: **chenyue-wang-usyd**
- GitHub Project: https://github.com/chenyue-wang-usyd/elec5305-project-540262760
- GitHub Pages: https://chenyue-wang-usyd.github.io/elec5305-project-540262760/

## 1. Project Overview

Recordings from phones and headsets often contain fan, traffic, or room noise, reducing listening comfort and potentially disrupting speech communication. This project will investigate single-channel audio enhancement using spectral subtraction. It will estimate background noise, attenuate contaminated frequency components, and reconstruct an enhanced waveform. Unlike a trained neural network, this approach requires no paired training dataset and exposes each processing stage for inspection. The deliverables are a reproducible Python prototype, comparative experiments, audio examples, and a documented GitHub demonstration. The central question is how subtraction strength and smoothing balance noise reduction against speech distortion.

## 2. Background and Motivation

The observation is modelled as y[n] = s[n] + d[n], where s is clean speech and d is additive noise. Boll's classical method estimates a noise spectrum during non-speech intervals and subtracts it from the observed spectrum [1]. Errors can leave isolated spectral peaks, heard as musical noise, or remove weak speech components. Over-subtraction and spectral flooring offer practical controls over this trade-off.

Martin's minimum-statistics estimator motivates a possible extension for changing noise [2]; it is not implemented in the current prototype. Hu and Loizou show why objective measures should be interpreted alongside perceived quality [3]. This topic connects windowing, Fourier analysis, power estimation, and reconstruction in a feasible semester project. Its limited complexity also makes failures easier to diagnose than those of a large learned model.

## 3. Proposed Methodology

Python, NumPy, SciPy, and Matplotlib will support processing, WAV input/output, and visualisation. Integer audio will be converted to floating point before averaging channels. The baseline uses a 32 ms Hann window and an 8 ms hop. The short-time Fourier transform (STFT) provides a spectrum Y(k,m) for frequency bin k and frame m. Its power is averaged over an initial 0.5-second noise-only region to estimate D. This assumes a known noise-only introduction and approximately stationary noise.

The target enhanced power is

`P_target = max(|Y|^2 - alpha |D|^2, beta |D|^2)`.

Here alpha controls over-subtraction and beta sets a residual-noise floor. A gain derived from this power is capped at one to avoid amplification and smoothed over neighbouring frames. Multiplication by the complex noisy spectrum retains its phase. Inverse STFT and overlap-add reconstruct the waveform; output peak scaling prevents clipping. The floor is therefore a target before gain clipping and smoothing, not a guaranteed final power bound.

A baseline with alpha = 1 and no smoothing will be compared with alpha values from 1 to 3, beta values from 0.005 to 0.05, and smoothing lengths from one to five frames. A fixed-seed synthetic signal already supports pipeline checks. Subsequent experiments will use appropriately licensed speech and noise, with NOIZEUS considered as a candidate corpus [3]. Dataset terms and provenance will be recorded before use. Utterances will be separated for tuning and final evaluation.

White, coloured, and recorded noise will be evaluated at input SNRs of -5, 0, 5, 10, and 15 dB. Noise mixtures will be calibrated over the scored speech region. Measurements will include input/output SNR, segmental SNR, and runtime, supplemented by spectrograms and listening comparisons. STOI or PESQ may be added if compatible implementations are available. Fixed seeds, saved parameters, and automatic figures will make results reproducible. Experiments will also examine failures when speech contaminates the noise estimate or background noise changes.

## 4. Expected Outcomes

The prototype will provide a WAV command-line interface, parameter controls, tests, generated examples, and clear documentation. The study should identify useful settings for stationary noise and quantify their distortion cost. Stronger subtraction is not assumed to improve every recording. Rapidly changing noise, inaccurate initial estimates, and retained noisy phase remain limitations. Current synthetic results demonstrate execution only; real-speech quality, intelligibility, and generalisation have not yet been established.

## AI Use Declaration

OpenAI ChatGPT and Codex assisted with drafting, implementation, debugging, reference checks, and formatting. Synthetic metrics are computed by the supplied code. The student remains responsible for reviewing the material and complying with course requirements before submission.

## 5. Timeline (Weeks 1-13)

| Week | Task |
|---|---|
| 1-2 | Confirm topic and scope. |
| 3-5 | Review literature and dataset terms. |
| 6-9 | Implement, test, and compare variants. |
| 10-11 | Evaluate parameters, quality, and runtime. |
| 12-13 | Complete report, documentation, and reproduction checks. |

## 6. References

1. S. F. Boll, "Suppression of Acoustic Noise in Speech Using Spectral Subtraction," *IEEE TASSP*, 27(2), 113-120, 1979. doi:10.1109/TASSP.1979.1163209.
2. R. Martin, "Noise Power Spectral Density Estimation Based on Optimal Smoothing and Minimum Statistics," *IEEE TSAP*, 9(5), 504-512, 2001. doi:10.1109/89.928915.
3. Y. Hu and P. C. Loizou, "Evaluation of Objective Measures for Speech Enhancement," *Interspeech*, 2006. doi:10.21437/Interspeech.2006-84.
