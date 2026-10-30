# Audio Processing Report 2

**Chenyue Wang | 540262760 | ELEC5305**

## Reproduce

1. Extract the entire ZIP to a writable folder.
2. Start MATLAB (tested with R2026a). No additional toolboxes are required.
3. Set MATLAB's current folder to `Report2 ChenyueWang`.
4. Open `Report2 ChenyueWang.mlx` and select **Run All**.
5. The script regenerates the experiment, figures, three WAV files, CSV and MAT results. Export the executed Live Script as PDF with code visible.

Alternatively, run `report_source.m` from this folder to reproduce the calculations and figures. This source has the same narrative and code as the Live Script. Do not use only a selection of sections before the experiment has been run.

## Contents

- `Report2 ChenyueWang.mlx`: principal editable MATLAB Live Script.
- `Report2 ChenyueWang.pdf`: PDF exported directly from the Live Script with execution enabled.
- `report_source.m`: plain-text narrative and executable source.
- `make_scene.m`: original deterministic synthesis and exact mixture calibration.
- `stereo_primary.m`: covariance estimation, Wiener projection and overlap-add.
- `run_experiment.m`: 45 evaluations, metrics, audio export and correctness assertions.
- `report_figures.m`: pipeline and experimental visualisations.
- `metrics.csv`: all individual trials, with five paired noise seeds.
- `experiment_results.mat`: full results and the illustrated example.
- `reference.wav`, `mixture.wav`, `primary.wav`: same example, same export scaling.

All required input signals are generated in code; no external data, course helper files, or download is required. Noise correlation is a population parameter; finite-sample realised correlation can differ. Metrics use unscaled in-memory signals, with one shared scale applied only when exporting the three WAV files.

The report focuses on Week 8 stereo decomposition and Week 6 overlap-add. It is an original simplified per-frequency-bin implementation, not a full reproduction of the course cochlear-band algorithm or a Week 10 binaural room simulation. Synthetic experiment outcomes are not subjective listening observations.

## Source and assistance attribution

Course concepts and external documentation are cited in Section 8. The report includes a transparent AI use declaration in Section 9. Review the report and declaration before submission. Keep the folder, Live Script and PDF names unchanged when preparing the final ZIP.
