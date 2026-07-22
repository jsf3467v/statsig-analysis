import numpy as np
import pytest
from scipy import stats

from experiment.stats import (
    cuped,
    power,
    sample_size,
    sprt,
    two_proportion,
    welch,
    winsorize,
)


def test_two_proportion_matches_hand_computation():
    r = two_proportion(200, 1000, 240, 1000)
    assert r.estimate == pytest.approx(0.04, abs=1e-9)
    assert r.p_value == pytest.approx(0.0309, abs=5e-4)
    assert r.ci_low == pytest.approx(0.00373, abs=5e-4)
    assert r.ci_high == pytest.approx(0.07627, abs=5e-4)
    assert r.significant


def test_two_proportion_empty_arm_raises():
    with pytest.raises(ValueError):
        two_proportion(0, 0, 5, 10)


def test_welch_matches_scipy():
    rng = np.random.default_rng(0)
    a, b = rng.normal(0, 1, 500), rng.normal(0.3, 1.2, 400)
    r = welch(a, b)
    t, p = stats.ttest_ind(b, a, equal_var=False)
    assert r.estimate == pytest.approx(b.mean() - a.mean(), abs=1e-12)
    assert r.p_value == pytest.approx(p, abs=1e-9)


def test_winsorize_clips_tails():
    v = np.array([0.0, 1, 2, 3, 4, 5, 6, 7, 8, 1000.0])
    w = winsorize(v, limit=0.1)
    assert w.max() < 1000
    assert w.max() == pytest.approx(np.percentile(v, 90))
    assert w.shape == v.shape


def test_sprt_decisions():
    assert sprt(90, 100, p0=0.5, p1=0.8) == "reject_h0"
    assert sprt(10, 100, p0=0.5, p1=0.8) == "accept_h0"
    assert sprt(6, 10, p0=0.5, p1=0.8) == "continue"
    with pytest.raises(ValueError):
        sprt(5, 10, p0=0.0, p1=0.8)


def test_sample_size_and_power_agree():
    n = sample_size(0.10, 0.02, alpha=0.05, power=0.8)
    assert n > 0
    assert power(0.10, 0.02, n) == pytest.approx(0.8, abs=0.02)
    assert sample_size(0.10, 0.04) < n  # larger effect needs fewer units


def test_power_monotonic_and_bounded():
    small, large = power(0.10, 0.02, 1000), power(0.10, 0.02, 50000)
    assert 0.0 <= small < large <= 1.0


def test_cuped_reduces_variance_preserves_mean():
    rng = np.random.default_rng(1)
    x = rng.normal(10, 3, 5000)
    y = 2 * x + rng.normal(0, 1, 5000)
    adjusted = cuped(y, x)
    assert adjusted.var() < y.var()
    assert adjusted.mean() == pytest.approx(y.mean(), abs=1e-9)
