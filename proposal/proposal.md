# Single-Channel Audio Noise Reduction Using Adaptive Spectral Subtraction

## Student Information

- Full Name: **Chenyue Wang**
- Student ID (SID): **540262760**
- GitHub Username: **chenyue-wang-usyd**
- GitHub Project: https://github.com/chenyue-wang-usyd/elec5305-project-540262760
- GitHub Pages: https://chenyue-wang-usyd.github.io/elec5305-project-540262760/

## 1. Project Overview

Everyday recordings made by phones, headsets, and embedded microphones are often corrupted by fan, traffic, or room noise. This reduces listening comfort and can also degrade speech communication and automatic speech recognition. This project will design and evaluate a single-channel noise-reduction system based on spectral subtraction. The method is attractive for a semester project because it is interpretable, computationally light, and can operate without paired training data. A noisy waveform will be divided into overlapping short-time frames, transformed to the frequency domain, and reduced by an estimated noise spectrum before reconstruction. The project will deliver a tested Python prototype, reproducible experiments, objective results, audio examples, and a documented GitHub Pages demonstration.

## 2. Background and Motivation

For additive noise, the observation can be modelled as y[n] = s[n] + d[n], where s[n] is clean speech and d[n] is noise. Boll's classical algorithm estimates the noise magnitude during non-speech intervals and subtracts it from each short-time speech spectrum [1]. It is efficient, but imperfect noise estimates can leave isolated time-frequency peaks known as musical noise. Straight subtraction can also remove weak speech components. These limitations create a useful engineering trade-off: stronger subtraction improves noise attenuation, while conservative subtraction better preserves speech.

Later work introduced over-subtraction and a spectral floor to control residual noise and speech distortion. Minimum-statistics noise tracking can follow changing noise without relying entirely on a voice-activity detector [2]. Multi-band subtraction further recognises that coloured noise affects frequency regions unequally [3]. Objective measures do not always agree with perceived quality, so a credible evaluation should combine signal measures with spectrograms and listening evidence [4]. I chose this topic because it connects core ELEC5305 concepts - sampling, windowing, the discrete Fourier transform, power spectra, filtering, and overlap-add reconstruction - in a system whose intermediate signals can be inspected and explained.

## 3. Proposed Methodology

The prototype will be implemented in Python using NumPy and SciPy for numerical signal processing, Matplotlib for figures, and standard WAV input/output. Mono audio will be normalised and segmented with a 32 ms Hann window and 8 ms hop. The short-time Fourier transform (STFT) produces Y(k,m), where k is frequency bin and m is frame index. An initial noise-only interval will provide the baseline noise power estimate. An optional minimum-statistics-style update will be investigated for slowly varying noise.

For each time-frequency bin, the enhanced power will be computed as

`|S_hat(k,m)|^2 = max(|Y(k,m)|^2 - alpha |D_hat(k,m)|^2, beta |D_hat(k,m)|^2)`.

Here alpha is the over-subtraction factor and beta is the spectral-floor coefficient. The corresponding gain will be smoothed across adjacent frames to reduce rapid isolated changes. The enhanced magnitude will be combined with the original noisy phase, then converted to the time domain by inverse STFT and overlap-add. Peak protection will prevent clipping. A transparent baseline with alpha = 1 and no gain smoothing will be compared against practical variants using alpha from 1.0 to 3.0, beta from 0.005 to 0.05, and one to five smoothing frames.

Experiments will use clean speech mixed with reproducible white, low-frequency, and real recorded noises at input SNRs of -5, 0, 5, 10, and 15 dB. The initial implementation includes a deterministic speech-like synthetic signal so that the complete pipeline can be tested without downloading a dataset. The main evaluation will use appropriately licensed speech/noise material, such as the NOIZEUS corpus described by Hu and Loizou [4], with source and licence documented. Files will be split by utterance so the same samples are not used to tune and report parameters.

Performance will be measured with input and output SNR, SNR improvement, segmental SNR, and processing time. Where compatible implementations are available, STOI and PESQ will supplement these measures. Waveform and spectrogram comparisons will show whether noise is removed uniformly or replaced by musical artefacts. A small informal listening comparison will record which parameter setting best balances residual noise and speech distortion. Scripts will fix random seeds, save parameters with results, and generate tables and figures automatically.

## 4. Expected Outcomes

The principal outcome will be a working command-line prototype that reads a WAV file, estimates noise from a nominated noise-only segment, writes enhanced audio, and exposes the main algorithm parameters. The repository will include unit tests, a reproducible demonstration, sample outputs, metric summaries, and clear instructions. I expect the method to improve SNR for stationary and slowly varying noise while using modest computation. Performance is expected to decline for rapidly changing noise or inaccurate noise-only estimates; this limitation will be measured rather than hidden. The final comparison should identify parameter ranges that reduce noise without excessive speech attenuation and explain the remaining musical-noise trade-off.

## 5. Timeline (Weeks 1-13)

| Week | Task |
|---|---|
| 1-2 | Confirm scope, success criteria, repository structure, and topic. |
| 3-5 | Review literature; select licensed speech/noise data; define metrics and baseline. |
| 6-7 | Implement WAV handling, STFT/ISTFT pipeline, noise estimation, and classical subtraction. |
| 8-9 | Add over-subtraction, spectral flooring, gain smoothing, tests, and automated plots. |
| 10-11 | Run parameter/noise/SNR experiments; analyse artefacts, runtime, and limitations. |
| 12 | Complete the report, audio examples, README, and GitHub Pages demonstration. |
| 13 | Reproduce all results from a clean environment; proofread and submit. |

## 6. References

1. S. F. Boll, "Suppression of Acoustic Noise in Speech Using Spectral Subtraction," *IEEE Transactions on Acoustics, Speech, and Signal Processing*, vol. 27, no. 2, pp. 113-120, 1979. doi:10.1109/TASSP.1979.1163209.
2. R. Martin, "Noise Power Spectral Density Estimation Based on Optimal Smoothing and Minimum Statistics," *IEEE Transactions on Speech and Audio Processing*, vol. 9, no. 5, pp. 504-512, 2001. doi:10.1109/89.928915.
3. S. D. Kamath and P. C. Loizou, "A Multi-Band Spectral Subtraction Method for Enhancing Speech Corrupted by Colored Noise," *Proceedings of ICASSP*, pp. IV-4160-IV-4164, 2002.
4. Y. Hu and P. C. Loizou, "Evaluation of Objective Measures for Speech Enhancement," *Proceedings of Interspeech*, pp. 1447-1450, 2006. doi:10.21437/Interspeech.2006-84.

## Appendix: Proposed Signal Flow

`Noisy WAV -> framing and Hann window -> STFT -> noise PSD estimate -> over-subtraction and floor -> gain smoothing -> noisy phase + enhanced magnitude -> inverse STFT/overlap-add -> enhanced WAV and metrics`
