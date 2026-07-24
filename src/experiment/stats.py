"""Frequentist experiment statistics: proportion and mean tests, sequential
testing, winsorization, power, and CUPED variance reduction."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log, sqrt

import numpy as np
from scipy import stats


@dataclass
class Result:
    metric: str
    estimate: float
    ci_low: float
    ci_high: float
    p_value: float
    significant: bool


def two_proportion(x_c: int, n_c: int, x_t: int, n_t: int, alpha: float = 0.05) -> Result:
    """Two-sided z-test on a conversion-rate difference (treatment - control)."""
    if n_c == 0 or n_t == 0:
        raise ValueError("each arm needs at least one unit")
    p_c, p_t = x_c / n_c, x_t / n_t
    diff = p_t - p_c
    pooled = (x_c + x_t) / (n_c + n_t)
    se_pool = sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_t))
    p_value = 2 * stats.norm.sf(abs(diff / se_pool)) if se_pool > 0 else 1.0
    se = sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    margin = stats.norm.ppf(1 - alpha / 2) * se
    return Result("conversion_diff", diff, diff - margin, diff + margin, p_value, p_value < alpha)


def welch(control: np.ndarray, treatment: np.ndarray, alpha: float = 0.05) -> Result:
    """Welch's unequal-variance t-test on a continuous metric."""
    c, t = np.asarray(control, float), np.asarray(treatment, float)
    if c.size < 2 or t.size < 2:
        raise ValueError("each arm needs at least two observations")
    diff = t.mean() - c.mean()
    vc, vt = c.var(ddof=1) / c.size, t.var(ddof=1) / t.size
    se = sqrt(vc + vt)
    if se == 0:
        return Result("mean_diff", diff, diff, diff, 1.0, False)
    dof = (vc + vt) ** 2 / (vc**2 / (c.size - 1) + vt**2 / (t.size - 1))
    p_value = 2 * stats.t.sf(abs(diff / se), dof)
    margin = stats.t.ppf(1 - alpha / 2, dof) * se
    return Result("mean_diff", diff, diff - margin, diff + margin, p_value, p_value < alpha)


def winsorize(values: np.ndarray, limit: float = 0.01) -> np.ndarray:
    """Clip both tails at the given quantile to blunt outliers."""
    v = np.asarray(values, float)
    low, high = np.percentile(v, [100 * limit, 100 * (1 - limit)])
    return np.clip(v, low, high)


def sprt(successes: int, trials: int, p0: float, p1: float,
         alpha: float = 0.05, beta: float = 0.2) -> str:
    """Wald sequential probability ratio test: reject_h0, accept_h0, or continue."""
    if not 0 < p0 < 1 or not 0 < p1 < 1:
        raise ValueError("p0 and p1 must be in (0, 1)")
    llr = successes * log(p1 / p0) + (trials - successes) * log((1 - p1) / (1 - p0))
    upper, lower = log((1 - beta) / alpha), log(beta / (1 - alpha))
    if llr >= upper:
        return "reject_h0"
    if llr <= lower:
        return "accept_h0"
    return "continue"


def sample_size(base_rate: float, mde: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Units per arm to detect an absolute lift `mde` on a proportion."""
    p2 = base_rate + mde
    if not 0 < base_rate < 1 or not 0 < p2 < 1:
        raise ValueError("base_rate and base_rate + mde must be in (0, 1)")
    z_a, z_b = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    pbar = (base_rate + p2) / 2
    num = z_a * sqrt(2 * pbar * (1 - pbar)) + z_b * sqrt(
        base_rate * (1 - base_rate) + p2 * (1 - p2))
    return ceil(num**2 / mde**2)


def power(base_rate: float, effect: float, n: int, alpha: float = 0.05) -> float:
    """Statistical power of a two-proportion test at `n` units per arm."""
    p2 = base_rate + effect
    se = sqrt(base_rate * (1 - base_rate) / n + p2 * (1 - p2) / n)
    if se == 0:
        return 0.0
    return float(stats.norm.cdf(abs(effect) / se - stats.norm.ppf(1 - alpha / 2)))


def cuped(metric: np.ndarray, covariate: np.ndarray) -> np.ndarray:
    """CUPED-adjust a metric using a pre-experiment covariate to cut variance."""
    y, x = np.asarray(metric, float), np.asarray(covariate, float)
    var_x = x.var(ddof=1)
    if var_x == 0:
        return y.copy()
    theta = np.cov(y, x, ddof=1)[0, 1] / var_x
    return y - theta * (x - x.mean())


def relative_lift(x_c: int, n_c: int, x_t: int, n_t: int, alpha: float = 0.05) -> Result:
    """Percent change in rate, treatment against control, by the delta method.

    Experimentation platforms report lift on this scale, so this is the form to
    compare against a platform result. The interval is built on the log ratio,
    which keeps it positive and asymmetric.
    """
    if n_c == 0 or n_t == 0:
        raise ValueError("each arm needs at least one unit")
    if x_c == 0 or x_t == 0:
        raise ValueError("each arm needs at least one converting unit")
    p_c, p_t = x_c / n_c, x_t / n_t
    ratio = p_t / p_c
    se_log = sqrt((1 - p_c) / x_c + (1 - p_t) / x_t)
    z = stats.norm.ppf(1 - alpha / 2)
    low, high = ratio * np.exp(-z * se_log), ratio * np.exp(z * se_log)
    p_value = 2 * stats.norm.sf(abs(log(ratio)) / se_log) if se_log > 0 else 1.0
    return Result("relative_lift_pct", 100 * (ratio - 1), 100 * (low - 1),
                  100 * (high - 1), p_value, p_value < alpha)
