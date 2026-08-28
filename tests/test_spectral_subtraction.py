from __future__ import annotations

import unittest

import numpy as np

from scripts.run_demo import make_demo, snr_db
from src.spectral_subtraction import spectral_subtract


class SpectralSubtractionTests(unittest.TestCase):
    def test_preserves_length_and_finite_values(self) -> None:
        rng = np.random.default_rng(1)
        signal = rng.normal(size=8000)
        result = spectral_subtract(signal, 16000, noise_duration=0.1)
        self.assertEqual(len(result), len(signal))
        self.assertTrue(np.all(np.isfinite(result)))

    def test_rejects_invalid_parameters(self) -> None:
        signal = np.ones(1000)
        with self.assertRaises(ValueError):
            spectral_subtract(signal, 16000, alpha=0.5)
        with self.assertRaises(ValueError):
            spectral_subtract(signal, 16000, beta=-0.1)
        with self.assertRaises(ValueError):
            spectral_subtract(signal, 0)

    def test_improves_stationary_noise_demo_snr(self) -> None:
        _, clean, noisy, active = make_demo()
        enhanced = spectral_subtract(noisy, 16000, noise_duration=0.5, alpha=2.0, beta=0.02)
        improvement = snr_db(clean, enhanced, active) - snr_db(clean, noisy, active)
        self.assertGreater(improvement, 2.0)


if __name__ == "__main__":
    unittest.main()

